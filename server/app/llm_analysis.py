import os
import pandas as pd
import numpy as np
import io
from pathlib import Path
from ydata_profiling import ProfileReport
from openai import OpenAI
from dotenv import load_dotenv
import re

load_dotenv()

# Initialize OpenAI client
OPENAI_API_KEY = os.getenv("OPEN_AI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPEN_AI_API_KEY environment variable is not set")

client = OpenAI(api_key=OPENAI_API_KEY)


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
        
        # Use LLM for better classification
        check_prompt = f"""Classify this user message into one of three categories:
1. "conversational" - casual chat, greetings, thanks, general conversation with no data request
2. "preliminary" - mentions dataset/data but is just stating intent (e.g., "I have a question about the dataset" without the actual question)
3. "analysis" - actual question or request requiring data analysis (e.g., "What patterns can we see?", "Analyze the trends")

User message: "{user_message}"

Respond with ONLY the category word: "conversational", "preliminary", or "analysis"."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You classify messages into 'conversational', 'preliminary', or 'analysis'. Respond with only one word."},
                {"role": "user", "content": check_prompt}
            ],
            temperature=0.1,
            max_tokens=15
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
    file_names: list[str]
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
        # Classify the message type
        message_type = await classify_message(user_message)
        
        # Handle conversational messages
        if message_type == "conversational":
            system_prompt = """You are a helpful AI assistant. Respond naturally and conversationally to the user's message. Keep responses brief and friendly."""
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content
        
        # Handle preliminary statements (e.g., "I have a question about the dataset")
        if message_type == "preliminary":
            system_prompt = """You are a helpful AI data analyst assistant. The user has indicated they want to ask about the dataset, but hasn't asked their specific question yet. Respond naturally and encouragingly, asking them what they'd like to know or analyze. Keep it brief and friendly."""
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            return response.choices[0].message.content
        
        # Load full datasets into pandas DataFrames (fast, server-side)
        dataframes = {}
        dataframe_info = {}
        
        for idx, (file_path, file_name) in enumerate(zip(file_paths, file_names)):
            df = pd.read_csv(file_path)
            # Create safe variable name from filename (shorter, cleaner)
            base_name = file_name.replace('.csv', '').lower()
            safe_name = re.sub(r'[^a-zA-Z0-9]', '_', base_name)
            safe_name = re.sub(r'_+', '_', safe_name).strip('_')
            
            # If multiple files, add index for clarity
            if len(file_paths) > 1:
                safe_name = f"df{idx+1}_{safe_name[:30]}"  # Limit length
            else:
                safe_name = f"df_{safe_name[:30]}"  # Still prefix with df for clarity
            
            dataframes[safe_name] = df
            dataframe_info[safe_name] = {
                'filename': file_name,
                'rows': len(df),
                'columns': list(df.columns),
                'shape': df.shape
            }
        
        # Build concise dataset summary (not full data)
        dataset_summary = "Available datasets:\n"
        for name, info in dataframe_info.items():
            dataset_summary += f"- {name}: {info['filename']} ({info['rows']} rows, {info['shape'][1]} columns: {', '.join(info['columns'][:10])})\n"
        
        # Define function for code execution
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "execute_analysis_code",
                    "description": "Execute Python code to analyze the datasets. Use pandas (pd) to work with the dataframes. The dataframes are loaded with safe names based on filenames. Return results using print() statements.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Python code to execute. Use print() to output results. DataFrames are available with names like 'democratic_vs_republican_votes_by_usa_state_2020' (based on filename)."
                            },
                            "explanation": {
                                "type": "string",
                                "description": "Brief explanation of what the code does"
                            }
                        },
                        "required": ["code", "explanation"]
                    }
                }
            }
        ]
        
        # Build the prompt
        system_prompt = f"""You are an expert data analyst specializing in qualitative research methods. 
Your role is to help users understand their datasets through qualitative analysis techniques.

{QUALITATIVE_METHODS_DESCRIPTION}

CRITICAL: When a user asks for "thematic analysis" or similar qualitative analysis of quantitative data:
- This is VALID and EXPECTED - qualitative methods can analyze patterns/themes in quantitative datasets
- Thematic analysis of voting data means identifying themes like: swing states, regional patterns, demographic trends, party strongholds, etc.
- DO NOT refuse or suggest alternatives - instead, perform the analysis by identifying themes and patterns in the data
- Use code execution to analyze the data and identify these themes
- Present your findings as themes/patterns you've identified

IMPORTANT INSTRUCTIONS:
1. When the user asks for analysis (thematic, content, pattern analysis, etc.):
   - Use the execute_analysis_code function to write and run Python/pandas code
   - The full datasets are loaded server-side - you have access to ALL rows, not just samples
   - Write code that performs the actual calculation/analysis
   - Use print() statements to output your results
   - For thematic analysis: identify themes in the data (e.g., swing states theme, regional patterns theme, etc.)
   
2. After executing code and seeing results:
   - Present the results clearly to the user
   - Frame quantitative patterns as qualitative themes when appropriate
   - Explain your methodology if asked
   - Be natural and conversational
   
3. Available dataframes (use these variable names in your code):
{dataset_summary}

4. Example code structure:
   - Calculate swing states: analyze vote margins
   - Filter data: df[df['column'] > value]
   - Aggregate: df.groupby('column').sum()
   - Print results: print(df.head()), print(list_of_states), etc.

IMPORTANT CODE WRITING RULES:
- Write complete, valid Python code
- Use print() statements to output results
- Don't use line continuation characters (\\) unnecessarily
- Make sure all strings are properly closed
- Use simple, straightforward code - avoid complex nested structures
- Test your logic mentally before writing the code

Answer naturally - don't force templates. NEVER refuse to do thematic analysis on quantitative data - instead, identify themes and patterns in the data itself."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        # Iterative conversation with code execution
        max_iterations = 5
        for iteration in range(max_iterations):
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=2000
            )
            
            message = response.choices[0].message
            
            # Convert message to dict format for messages list
            message_dict = {
                "role": message.role,
                "content": message.content
            }
            
            # Add tool calls if present
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
            
            # Check if LLM wants to execute code
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    if tool_call.function.name == "execute_analysis_code":
                        import json
                        function_args = json.loads(tool_call.function.arguments)
                        code = function_args.get("code", "")
                        explanation = function_args.get("explanation", "")
                        
                        # Execute the code
                        output, success = await execute_safe_code(code, dataframes)
                        
                        # Add function result to conversation
                        tool_message = {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": f"Code executed successfully:\n{output}" if success else f"Code execution failed:\n{output}"
                        }
                        messages.append(tool_message)
                continue  # Continue loop to get LLM's response with results
            
            # No tool calls - LLM is ready to respond
            if message.content:
                return message.content
            else:
                # Fallback if no content
                return "Analysis completed. Please rephrase your question if you need more information."
        
        # Fallback if max iterations reached
        last_message = messages[-1] if messages else None
        if last_message and isinstance(last_message, dict):
            return last_message.get("content", "Analysis completed.")
        return "Analysis completed."
        
    except Exception as e:
        raise Exception(f"Error in LLM analysis: {str(e)}")

