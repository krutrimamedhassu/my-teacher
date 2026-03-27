from app.logger.app_logger import app_logger

def extract_json_from_codeblock(text: str) -> str:
    app_logger.log_debug(f"[EndpointUtils] Starting extract_json_from_codeblock with text length: {len(text)}")
    try:
        # Remove triple backticks and optional 'json' after them
        original_text = text
        if text.strip().startswith("```"):
            app_logger.log_debug("[EndpointUtils] Text contains code block markers, extracting JSON")
            text = text.strip()
            # Remove the first line (```json or ```)
            lines = text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
                app_logger.log_debug("[EndpointUtils] Removed opening code block marker")
            # Remove the last line if it's ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
                app_logger.log_debug("[EndpointUtils] Removed closing code block marker")
            result = "\n".join(lines)
            app_logger.log_debug(f"[EndpointUtils] Successfully extracted JSON from code block, result length: {len(result)}")
            return result
        app_logger.log_debug("[EndpointUtils] No code block markers found, returning original text")
        return text
    except Exception as e:
        app_logger.log_error(f"[EndpointUtils] Error in extract_json_from_codeblock: {str(e)}")
        return text  # Return original text on error