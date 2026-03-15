from __future__ import annotations

import os
import pandas as pd
import numpy as np
import json
from openai import OpenAI
from dotenv import load_dotenv
import re

load_dotenv()

from .llm_providers import complete_chat, get_active_provider_name


# ---------------------------------------------------------------------------
# Shared context builders for EDA and benchmarking
# ---------------------------------------------------------------------------

OPENAI_API_KEY = os.getenv("OPEN_AI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


QUALITATIVE_METHODS_DESCRIPTION = """
Qualitative Analysis Methods Available:

1. **Thematic Analysis**
   - Identifies, analyzes, and reports patterns (themes) within data
   - Works with BOTH qualitative and quantitative datasets
   - For quantitative data: identifies themes in patterns (e.g., regional voting themes, demographic themes, swing state themes)
   - Codes and groups recurring patterns into themes representing significant concepts
   - Example: In voting data, themes could be "swing states", "party strongholds", "regional patterns", "urban vs rural divides"

2. **Content Analysis**
   - Systematic method to quantify and interpret presence of patterns, trends, or concepts
   - Analyzes frequency patterns, trends, and relationships in data
   - Can be quantitative (counting) or qualitative (interpreting meanings)
   - Example: Analyzing frequency of voting patterns, turnout trends, or electoral outcomes

3. **Narrative Analysis**
   - Examines patterns and sequences in data to understand how events or trends unfold
   - For quantitative data: analyzes the "story" the data tells (e.g., election narrative, voting trend narratives)
   - Analyzes structure, sequence, and meaning of data patterns
   - Reveals how data points create meaningful narratives or stories

4. **Grounded Theory**
   - Develops new theories directly grounded in collected data
   - Builds theoretical models through analysis of patterns and relationships
   - Creates explanations supported by evidence from the data itself
   - Example: Developing a theory about voter behavior based on voting patterns observed

5. **Discourse Analysis**
   - Explores how patterns in data reflect broader social, political, or cultural contexts
   - Examines relationships between data patterns and their contextual meaning
   - Reveals how data reflects and shapes social realities
   - Example: Analyzing how voting patterns reflect political discourse and social dynamics

IMPORTANT: These methods can be applied to quantitative datasets. For example, thematic analysis of voting data means identifying themes like "swing states", "regional voting patterns", "demographic trends", etc. When asked for thematic analysis, identify meaningful themes and patterns in the data itself.
"""


def _prepare_dataframe_context(file_paths: list[str], file_names: list[str]):
    """
    Load CSV files into pandas DataFrames and return shared context structures.
    
    Returns:
        tuple of (dataframes_dict, metadata_dict, dataset_summary_str)
    """
    dataframes = {}
    dataframe_info = {}
    summary_lines = []
    
    for idx, (file_path, file_name) in enumerate(zip(file_paths, file_names)):
        df = pd.read_csv(file_path)
        base_name = file_name.replace('.csv', '').lower()
        safe_name = re.sub(r'[^a-zA-Z0-9]', '_', base_name)
        safe_name = re.sub(r'_+', '_', safe_name).strip('_')
        
        if len(file_paths) > 1:
            safe_name = f"df{idx+1}_{safe_name[:30]}"
        else:
            safe_name = f"df_{safe_name[:30]}"
        
        dataframes[safe_name] = df
        dataframe_info[safe_name] = {
            "filename": file_name,
            "rows": len(df),
            "columns": list(df.columns),
            "shape": df.shape
        }
        summary_lines.append(
            f"- {safe_name}: {file_name} ({len(df)} rows, {df.shape[1]} columns: {', '.join(list(df.columns)[:10])})"
        )
    
    dataset_summary = "Available datasets:\n" + "\n".join(summary_lines)
    return dataframes, dataframe_info, dataset_summary


def build_context_block(
    file_paths: list[str],
    file_names: list[str],
    context_mode: str,
) -> tuple[str, dict[str, pd.DataFrame]]:
    """
    Build a text context block describing the datasets at different levels.

    Returns a tuple of (context_text, dataframes_dict) so callers that need
    in-memory DataFrames (e.g. quantitative analysis) can reuse the same load.
    """
    # Always prepare the base structures once
    dataframes, dataframe_info, dataset_summary = _prepare_dataframe_context(file_paths, file_names)

    if context_mode == "none":
        return "", dataframes

    if context_mode == "light":
        # Light context: high-level dataset summary only
        header = "Dataset context (light):\n"
        return header + dataset_summary, dataframes

    # Rich context: dataset summary + qualitative column-level insights
    qualitative_context = _build_qualitative_context(dataframes)
    rich_parts = [
        "Dataset context (rich):",
        dataset_summary,
        "",
        qualitative_context,
    ]
    return "\n".join(rich_parts), dataframes


async def generate_data_profile(file_path: str) -> dict:
    """
    Generate a data profile using ydata-profiling and return key insights.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        Dictionary containing profile summary and insights
    """
    try:
        # Read the CSV file
        df = pd.read_csv(file_path)

        # Import here to avoid loading heavy dependency unless needed
        try:
            from ydata_profiling import ProfileReport
        except Exception as exc:
            raise RuntimeError("ydata-profiling is required to generate data profiles") from exc
        
        # Generate profile report for additional insights
        profile = ProfileReport(df, title="Data Profile", minimal=True)
        
        # Build a comprehensive summary using both pandas and profile report
        total_missing = df.isnull().sum().sum()
        summary = {
            "number_of_variables": len(df.columns),
            "number_of_observations": len(df),
            "total_missing": int(total_missing),
            "memory_size": f"{df.memory_usage(deep=True).sum() / 1024:.2f} KB",
            "columns": []
        }
        
        # Extract column-level information
        for col_name in df.columns:
            col = df[col_name]
            missing_count = col.isnull().sum()
            missing_percentage = (missing_count / len(df)) * 100 if len(df) > 0 else 0
            unique_count = col.nunique()
            
            col_summary = {
                "name": col_name,
                "type": str(col.dtype),
                "missing_count": int(missing_count),
                "missing_percentage": round(missing_percentage, 2),
                "unique_count": int(unique_count),
            }
            
            # Add type-specific information
            if pd.api.types.is_numeric_dtype(col):
                col_summary["mean"] = float(col.mean()) if not col.empty else None
                col_summary["std"] = float(col.std()) if not col.empty else None
                col_summary["min"] = float(col.min()) if not col.empty else None
                col_summary["max"] = float(col.max()) if not col.empty else None
            elif pd.api.types.is_string_dtype(col) or pd.api.types.is_object_dtype(col):
                # For text/string columns, get sample values for qualitative analysis
                sample_values = col.dropna().head(5).tolist()
                col_summary["sample_values"] = [str(v) for v in sample_values]
            
            summary["columns"].append(col_summary)
        
        # Add sample data preview (first 10 rows as text for qualitative analysis)
        sample_rows = df.head(10).to_dict('records')
        # Convert sample rows to string format for better LLM processing
        summary["sample_data"] = [
            {str(k): str(v) if pd.notna(v) else "N/A" for k, v in row.items()} 
            for row in sample_rows
        ]
        
        return summary
        
    except Exception as e:
        raise Exception(f"Error generating profile: {str(e)}")


def _format_number(value: float) -> str:
    """Consistently format numeric values for qualitative summaries."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "N/A"
    try:
        float_value = float(value)
    except (TypeError, ValueError):
        return str(value)
    if abs(float_value) >= 1000 or float_value.is_integer():
        return f"{float_value:,.0f}"
    return f"{float_value:,.2f}".rstrip("0").rstrip(".")


def _summarize_numeric_column(series: pd.Series, column_name: str) -> str | None:
    """Create a compact textual summary for numeric columns."""
    numeric_series = pd.to_numeric(series, errors='coerce').dropna()
    if numeric_series.empty:
        return None
    desc = numeric_series.describe()
    quantiles = numeric_series.quantile([0.25, 0.5, 0.75])
    highs = numeric_series.sort_values(ascending=False).head(3).tolist()
    lows = numeric_series.sort_values(ascending=True).head(3).tolist()
    return (
        f"{column_name}: mean { _format_number(desc['mean']) }, "
        f"median { _format_number(quantiles.loc[0.5]) }, "
        f"range { _format_number(desc['min']) } → { _format_number(desc['max']) }. "
        f"Highest values around {', '.join(_format_number(v) for v in highs)}; "
        f"lowest around {', '.join(_format_number(v) for v in lows)}."
    )


def _summarize_categorical_column(series: pd.Series, column_name: str) -> str | None:
    """Create qualitative summary text for categorical columns."""
    cleaned = series.dropna().astype(str)
    if cleaned.empty:
        return None
    value_counts = cleaned.value_counts().head(5)
    total_unique = cleaned.nunique()
    top_values = ", ".join(
        f"{val} ({count})" for val, count in value_counts.items()
    )
    return (
        f"{column_name}: {total_unique} unique values. "
        f"Most common → {top_values}."
    )


def _build_qualitative_context(dataframes: dict[str, pd.DataFrame]) -> str:
    """Generate qualitative-friendly summaries for every dataframe."""
    sections: list[str] = []
    for df_name, df in dataframes.items():
        lines = [
            f"Dataset {df_name}: {len(df)} rows, {len(df.columns)} columns.",
            "Column highlights:"
        ]
        column_insights: list[str] = []
        for column in df.columns:
            series = df[column]
            if pd.api.types.is_numeric_dtype(series):
                summary = _summarize_numeric_column(series, column)
            else:
                summary = _summarize_categorical_column(series, column)
            if summary:
                column_insights.append(f"- {summary}")
        if column_insights:
            lines.extend(column_insights[:8])  # keep context concise
        else:
            lines.append("- No column insights available.")
        sample_rows = df.head(3).to_dict('records')
        sample_text = json.dumps(sample_rows, default=str)[:800]
        lines.append(f"Sample rows (truncated): {sample_text}")
        sections.append("\n".join(lines))
    return "\n\n".join(sections)


async def classify_message(user_message: str) -> str:
    """
    Classify the user message into one of three categories:
    - "conversational": casual chat, greetings, thanks
    - "preliminary": mentions dataset but no actual question yet (e.g., "I have a question about the dataset")
    - "analysis": actual question requiring dataset analysis
    
    Args:
        user_message: User's message
        
    Returns:
        "conversational", "preliminary", or "analysis"
    """
    try:
        message_lower = user_message.lower().strip()
        
        # Check if message is clearly conversational (short greetings, thanks, etc.)
        conversational_keywords = [
            'thank', 'thanks', 'hello', 'hi', 'hey', 'bye', 'goodbye', 
            'ok', 'okay', 'sure', 'yes', 'no', 'cool', 'nice', 'great',
            'got it', 'understood', 'perfect', 'awesome', 'wow', 'nothing much',
            'how about you', "what's on your mind"
        ]
        
        # If message is very short and matches conversational patterns
        if len(message_lower.split()) <= 5 and any(keyword in message_lower for keyword in conversational_keywords):
            return "conversational"
        
        # Check for preliminary statements (mentions dataset but no actual question)
        # These are very specific patterns that are clearly just stating intent
        strict_preliminary_patterns = [
            'i have a question',
            'i have questions',
            'i want to ask',
            'can i ask',
            'i\'d like to ask',
        ]
        
        # Check if it's just a preliminary statement without an actual question
        question_words = ['what', 'why', 'how', 'when', 'where', 'which', 'who', 'can you', 'show me', 'identify', 'find', 'analyze', 'compare', 'calculate']
        has_question_word = any(word in message_lower for word in question_words)
        has_question_mark = '?' in message_lower
        
        # Only treat as preliminary if it matches strict patterns AND has no question words/marks
        is_strict_preliminary = any(pattern in message_lower for pattern in strict_preliminary_patterns)
        
        # If it's a strict preliminary pattern AND has no question indicators, it's preliminary
        # Otherwise, if it has question words/marks or action verbs, it's likely analysis
        if is_strict_preliminary and not (has_question_word or has_question_mark):
            return "preliminary"
        
        # Use LLM for better classification when OpenAI is available
        check_prompt = f"""Classify this user message into one of three categories:
1. "conversational" - casual chat, greetings, thanks, general conversation with no data request
2. "preliminary" - mentions dataset/data but is just stating intent (e.g., "I have a question about the dataset" without the actual question)
3. "analysis" - actual question or request requiring data analysis (e.g., "What patterns can we see?", "Analyze the trends")

User message: "{user_message}"

Respond with ONLY the category word: "conversational", "preliminary", or "analysis"."""

        if client is None:
            return "analysis"

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You classify messages into 'conversational', 'preliminary', or 'analysis'. Respond with only one word.",
                },
                {"role": "user", "content": check_prompt},
            ],
            max_completion_tokens=15,
        )

        result = response.choices[0].message.content.strip().lower()
        if "preliminary" in result:
            return "preliminary"
        elif "conversational" in result:
            return "conversational"
        else:
            return "analysis"
        
    except Exception as e:
        # If check fails, default to analysis to be safe
        return "analysis"


async def execute_safe_code(code: str, dataframes: dict[str, pd.DataFrame]) -> tuple[str, bool]:
    """
    Safely execute Python code with access to dataframes.
    Only allows pandas, numpy, and basic Python operations.
    
    Args:
        code: Python code to execute
        dataframes: Dictionary of dataframe_name -> DataFrame
        
    Returns:
        Tuple of (output_string, success_boolean)
    """
    # Restricted globals - only allow safe operations
    safe_builtins = {
        'abs': abs, 'all': all, 'any': any, 'bool': bool, 'dict': dict,
        'enumerate': enumerate, 'float': float, 'int': int, 'len': len,
        'list': list, 'max': max, 'min': min, 'range': range, 'round': round,
        'sorted': sorted, 'str': str, 'sum': sum, 'tuple': tuple, 'zip': zip,
        'print': print,
    }
    
    restricted_globals = {
        '__builtins__': safe_builtins,
        'pd': pd,
        'pandas': pd,
        'np': np,
        'numpy': np,
        **dataframes  # Add dataframes to namespace
    }
    
    # Remove dangerous operations from code
    dangerous_patterns = [
        r'__import__', r'eval', r'exec', r'compile', r'open', r'file',
        r'input', r'raw_input', r'globals', r'locals', r'vars',
        r'dir', r'hasattr', r'setattr', r'delattr', r'getattr',
    ]
    
    code_lower = code.lower()
    for pattern in dangerous_patterns:
        if re.search(pattern, code_lower):
            return f"Error: Code contains restricted operation: {pattern}", False
    
    try:
        # First, try to compile the code to catch syntax errors early
        try:
            compile(code, '<string>', 'exec')
        except SyntaxError as syn_err:
            return f"Syntax error in code (line {syn_err.lineno}): {syn_err.msg}\n{syn_err.text}", False
        except Exception as compile_err:
            return f"Error compiling code: {str(compile_err)}", False
        
        # Capture stdout and any return value
        import sys
        from io import StringIO
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        # Wrap code to capture return value (but don't use f-string to avoid issues)
        wrapped_code = "_result = None\n" + code
        
        # Execute code
        try:
            exec(wrapped_code, restricted_globals, restricted_globals)
        except Exception as exec_err:
            sys.stdout = old_stdout
            error_msg = str(exec_err)
            # Try to get more context about the error
            import traceback
            tb_str = ''.join(traceback.format_exception(type(exec_err), exec_err, exec_err.__traceback__))
            # Limit traceback length
            if len(tb_str) > 2000:
                tb_str = tb_str[:2000] + "... (truncated)"
            return f"Error executing code: {error_msg}\n\nTraceback:\n{tb_str}", False
        
        # Get return value if exists
        result_value = restricted_globals.get('_result')
        
        # Restore stdout
        sys.stdout = old_stdout
        output = captured_output.getvalue()
        
        # Combine print output and return value
        if result_value is not None:
            result_str = str(result_value)
            # Limit very long outputs
            if len(result_str) > 5000:
                result_str = result_str[:5000] + f"\n... (truncated, {len(result_str)} chars total)"
            output += f"\nReturn value: {result_str}"
        
        # Limit output size to avoid token limits
        if len(output) > 10000:
            output = output[:10000] + f"\n... (output truncated, total length: {len(output)} chars)"
        
        # If code didn't print anything, show a summary
        if not output.strip():
            # Try to find common variable names that might have results
            df_vars = {k: v for k, v in restricted_globals.items() if isinstance(v, pd.DataFrame)}
            if df_vars:
                output = f"Code executed. DataFrames available: {list(df_vars.keys())}"
            else:
                output = "Code executed successfully (no output captured)"
        
        return output, True
        
    except Exception as e:
        import sys
        sys.stdout = old_stdout
        import traceback
        error_detail = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
        if len(error_detail) > 1000:
            error_detail = error_detail[:1000] + "... (truncated)"
        return f"Unexpected error: {str(e)}\n\n{error_detail}", False


async def analyze_with_llm_qualitative(
    user_message: str,
    file_paths: list[str],
    file_names: list[str],
    provider: str | None = None,
    model: str | None = None,
) -> str:
    """
    Perform qualitative analysis on the selected datasets using LLM.
    Handles conversational, preliminary, and analysis requests appropriately.
    
    Args:
        user_message: User's question or query
        file_paths: List of paths to selected CSV files
        file_names: List of corresponding file names
        
    Returns:
        LLM response string
    """
    try:
        # Classify the message type (always uses OpenAI when available)
        message_type = await classify_message(user_message)
        
        # Handle conversational messages
        if message_type == "conversational":
            system_prompt = (
                "You are a helpful AI assistant. Respond naturally and conversationally to the user's message. "
                "Keep responses brief and friendly."
            )

            text = await complete_chat(
                provider,
                system_prompt=system_prompt,
                user_prompt=user_message,
                model=model,
                temperature=0.7,
                max_tokens=500,
            )

            return text
        
        # Handle preliminary statements (e.g., "I have a question about the dataset")
        if message_type == "preliminary":
            system_prompt = (
                "You are a helpful AI data analyst assistant. The user has indicated they want to ask about "
                "the dataset, but hasn't asked their specific question yet. Respond naturally and encouragingly, "
                "asking them what they'd like to know or analyze. Keep it brief and friendly."
            )

            text = await complete_chat(
                provider,
                system_prompt=system_prompt,
                user_prompt=user_message,
                model=model,
                temperature=0.7,
                max_tokens=300,
            )

            return text
        
        # Load datasets and build qualitative summaries (no tool execution needed)
        dataframes, _, dataset_summary = _prepare_dataframe_context(file_paths, file_names)
        qualitative_context = _build_qualitative_context(dataframes)
        
        system_prompt = (
            "You are an expert data analyst specializing in qualitative research methods.\n"
            "Your job is to interpret structured dataset summaries and craft narrative, theme-based findings.\n\n"
            f"{QUALITATIVE_METHODS_DESCRIPTION}\n\n"
            "Guidelines:\n"
            '- Treat numeric trends as qualitative stories (e.g., "emerging regions", "outlier segments").\n'
            "- Always cite evidence from the provided summaries (column names, relative magnitudes, notable values).\n"
            "- Highlight at least three insights, each with a short explanation of why it matters.\n"
            "- Mention relevant limitations or missing context if the data cannot fully answer the question.\n"
            "- Stay natural and conversational—avoid rigid templates."
        )

        user_prompt = (
            f"User request:\n{user_message}\n\n"
            f"Dataset overview:\n{dataset_summary}\n\n"
            f"Detailed qualitative context:\n{qualitative_context}\n\n"
            "Please respond with qualitative analysis that:\n"
            "1. Directly answers the user's question.\n"
            "2. Names each key theme and describes the supporting evidence.\n"
            "3. Explains implications or recommended next questions.\n"
            "4. Notes any data gaps or assumptions when appropriate."
        )

        text = await complete_chat(
            provider,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=model,
            temperature=0.6,
            max_tokens=1800,
        )

        return text.strip()
        
    except Exception as e:
        raise Exception(f"Error in LLM analysis: {str(e)}")


async def analyze_with_llm_quantitative(
    user_message: str,
    file_paths: list[str],
    file_names: list[str],
    provider: str | None = None,
    model: str | None = None,
) -> dict:
    """
    Perform quantitative/EDA analysis using LLM-generated Python code.
    
    Returns dictionary with response text, code, output, and execution metadata.
    """
    try:
        dataframes, dataframe_info, dataset_summary = _prepare_dataframe_context(file_paths, file_names)
        
        active_provider = get_active_provider_name(provider)
        
        # For non-OpenAI providers, fall back to a descriptive, narrative-style analysis
        if active_provider != "openai" or client is None:
            qualitative_text = await analyze_with_llm_qualitative(
                user_message=user_message,
                file_paths=file_paths,
                file_names=file_names,
                provider=provider,
                model=model,
            )
            return {
                "response": qualitative_text,
                "code": None,
                "code_explanation": "Code execution is currently only available with the OpenAI provider.",
                "data_output": "",
                "code_success": False,
                "code_error": "Code execution is only supported when using the OpenAI provider.",
            }

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "execute_analysis_code",
                    "description": "Execute pandas/numpy code against the loaded CSV dataframes. Use print() to show tabular results or summaries.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Executable Python code that references provided dataframe names."
                            },
                            "explanation": {
                                "type": "string",
                                "description": "A short explanation of the analysis the code performs."
                            }
                        },
                        "required": ["code", "explanation"]
                    }
                }
            }
        ]
        
        system_prompt = f"""You are a senior data scientist performing exploratory quantitative analysis.
You have server-side access to complete datasets loaded as pandas DataFrames with these names:
{dataset_summary}

Follow this workflow:
1. Read the user's quantitative question carefully.
2. Devise a concise pandas analysis plan (group-bys, aggregations, descriptive stats, etc.).
3. Call execute_analysis_code with clean, reproducible Python code that:
   - Imports are unnecessary (pd/np already provided)
   - Uses print() to show findings and tables
   - Avoids long triple-quoted strings
4. After seeing the tool output, explain the findings in natural language, referencing concrete numbers.

Always call execute_analysis_code at least once before giving your final answer.
If code execution fails, inspect the error, adjust the code, and try again.
Keep responses focused on EDA insights (trends, comparisons, distributions)."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        last_code = None
        last_explanation = ""
        last_output = ""
        last_success = False
        last_error = None
        
        max_iterations = 6
        for _ in range(max_iterations):
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=tools,
                tool_choice="auto",
                max_completion_tokens=1800
            )
            
            message = response.choices[0].message
            message_dict = {
                "role": message.role,
                "content": message.content
            }
            
            if message.tool_calls:
                message_dict["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]
            
            messages.append(message_dict)
            
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    if tool_call.function.name != "execute_analysis_code":
                        continue
                    
                    function_args = json.loads(tool_call.function.arguments)
                    code = function_args.get("code", "")
                    explanation = function_args.get("explanation", "")
                    
                    output, success = await execute_safe_code(code, dataframes)
                    last_code = code
                    last_explanation = explanation
                    last_output = output
                    last_success = success
                    last_error = None if success else output
                    
                    tool_message = {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": f"Code executed successfully:\n{output}" if success else f"Code execution failed:\n{output}"
                    }
                    messages.append(tool_message)
                continue
            
            final_content = message.content or "Analysis complete."
            return {
                "response": final_content,
                "code": last_code,
                "code_explanation": last_explanation,
                "data_output": last_output,
                "code_success": last_success,
                "code_error": last_error if not last_success else None
            }
        
        return {
            "response": "Analysis completed.",
            "code": last_code,
            "code_explanation": last_explanation,
            "data_output": last_output,
            "code_success": last_success,
            "code_error": last_error if not last_success else None
        }
    
    except Exception as e:
        raise Exception(f"Error in quantitative LLM analysis: {str(e)}")


async def run_timed_analysis(
    *,
    analysis_type: str,
    user_message: str,
    file_paths: list[str],
    file_names: list[str],
    provider: str | None = None,
    model: str | None = None,
    context_mode: str = "none",
) -> dict:
    """
    Wrapper used by the benchmark endpoint to:
    - Build a context block (none/light/rich)
    - Call the appropriate qualitative/quantitative analysis function
    - Measure end-to-end latency in milliseconds
    - Return a structured result dictionary
    """
    # Build context and keep dataframes in memory when needed
    context_block, _ = build_context_block(file_paths, file_names, context_mode)

    if context_block:
        augmented_message = (
            f"{context_block}\n\n"
            f"User question:\n{user_message}"
        )
    else:
        augmented_message = user_message

    start = pd.Timestamp.utcnow()

    if analysis_type == "qualitative":
        response_text = await analyze_with_llm_qualitative(
            user_message=augmented_message,
            file_paths=file_paths,
            file_names=file_names,
            provider=provider,
            model=model,
        )
        end = pd.Timestamp.utcnow()
        latency_ms = (end - start).total_seconds() * 1000.0

        return {
            "analysis_type": analysis_type,
            "provider": provider,
            "model": model,
            "context_mode": context_mode,
            "latency_ms": latency_ms,
            "response": response_text,
            "files_analyzed": file_names,
            "code": None,
            "code_explanation": None,
            "data_output": "",
            "code_success": None,
            "code_error": None,
        }

    if analysis_type == "quantitative":
        quant_result = await analyze_with_llm_quantitative(
            user_message=augmented_message,
            file_paths=file_paths,
            file_names=file_names,
            provider=provider,
            model=model,
        )
        end = pd.Timestamp.utcnow()
        latency_ms = (end - start).total_seconds() * 1000.0

        return {
            "analysis_type": analysis_type,
            "provider": provider,
            "model": model,
            "context_mode": context_mode,
            "latency_ms": latency_ms,
            "response": quant_result.get("response"),
            "files_analyzed": file_names,
            "code": quant_result.get("code"),
            "code_explanation": quant_result.get("code_explanation"),
            "data_output": quant_result.get("data_output"),
            "code_success": quant_result.get("code_success"),
            "code_error": quant_result.get("code_error"),
        }

    # Fallback for unknown analysis types
    end = pd.Timestamp.utcnow()
    latency_ms = (end - start).total_seconds() * 1000.0
    return {
        "analysis_type": analysis_type,
        "provider": provider,
        "model": model,
        "context_mode": context_mode,
        "latency_ms": latency_ms,
        "response": f"Unsupported analysis_type: {analysis_type}",
        "files_analyzed": file_names,
        "code": None,
        "code_explanation": None,
        "data_output": "",
        "code_success": False,
        "code_error": f"Unsupported analysis_type: {analysis_type}",
    }

