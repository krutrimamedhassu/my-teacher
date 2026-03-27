from typing import Dict, Any, List
from app.logger.app_logger import app_logger


class ToolRegistry:
    """
    Registry for managing all available tools and their configurations.
    Centralizes tool definitions and provides validation.
    """

    TOOLS: Dict[str, Dict[str, Any]] = {
        "document_query": {
            "endpoint": "/api/v1/document-qa/query",
            "description": "Search through uploaded documents to find relevant information. Ask the user how many results they want and whether to search all documents or specific ones.",
            "schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "search_all": {"type": "boolean"},
                    "max_results": {"type": "integer"},
                    "conversation_id": {"type": "string", "description": "Optional conversation ID for context"},
                },
                "required": ["query", "search_all", "max_results"],
            }
        },
        "generate_flashcards": {
            "endpoint": "/api/v1/flashcards/",
            "description": "Generate flashcards from educational content. Ask the user for subject area, difficulty level (beginner/intermediate/advanced), and number of cards desired before generating.",
            "schema": {
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "subject_area": {"type": "string"},
                    "difficulty_level": {"type": "string"},
                    "num_cards": {"type": "integer"},
                },
                "required": ["content", "subject_area", "difficulty_level", "num_cards"],
            },
        },
        "topic_breakdown": {
            "endpoint": "/api/v1/breakdowns/topic-breakdown/",
            "description": "Break down complex content into organized topics and subtopics. Ask the user for the subject area to provide better context and organization.",
            "schema": {
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "subject_area": {"type": "string"},
                },
                "required": ["content", "subject_area"],
            },
        },
        "explain_concept": {
            "endpoint": "/api/v1/explanations/explain",
            "description": "Explain concepts using different personas and teaching styles. Ask the user for subject area, student level (beginner/intermediate/advanced), and preferred persona. When using celebrity persona, ask which celebrity they want.",
            "schema": {
                "type": "object",
                "properties": {
                    "concept": {"type": "string"},
                    "persona": {
                        "type": "string",
                        "description": "Persona for explanation. Use 'celebrity' for celebrity/character explanations, or choose from: expert_professor, relatable_tutor, storyteller, visual_explainer, exam_coach"
                    },
                    "subject_area": {"type": "string"},
                    "student_level": {"type": "string"},
                    "celebrity_name": {
                        "type": "string",
                        "description": "Required when persona is 'celebrity'. The name of the celebrity or character (e.g., 'spider man', 'iron man', 'einstein')"
                    },
                },
                "required": ["concept", "subject_area", "persona", "student_level"],
            },
        },
        "extract_key_concepts": {
            "endpoint": "/api/v1/key-concepts/extract-key-concepts",
            "description": "Extract key concepts, definitions, formulas, and relationships from educational content. Ask the user for the subject area to provide better context.",
            "schema": {
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "subject_area": {"type": "string"},
                },
                "required": ["content", "subject_area"],
            },
        },
        "generate_mcq_set": {
            "endpoint": "/api/v1/multiple-choice-questions/",
            "schema": {
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "subject_area": {"type": "string"},
                    "difficulty_level": {"type": "string"},
                    "num_mcqs": {"type": "integer"},
                },
                "required": ["content", "subject_area", "difficulty_level", "num_mcqs"],
            },
            "description": "Generate multiple choice questions (MCQs) from educational content. Ask the user for subject area, difficulty level (beginner/intermediate/advanced), number of questions, and question types before generating.",
            "prompt_name": "mcq"
        },
        "generate_question_paper": {
            "endpoint": "/api/v1/qa/",
            "schema": {
                "type": "object",
                "properties": {
                    "document_id": {"type": "string"},
                    "content": {"type": "string"},
                    "context": {"type": "string"},
                    "num_pairs": {"type": "integer"},
                },
                "required": ["num_pairs"],
            },
            "description": "Generate question and answer pairs from educational content. Ask the user how many question pairs they want and what type of questions (short answer, essay, etc.) before generating."
        },
        "study_plan": {
            "endpoint": "/api/v1/study-plan",
            "description": "Create a personalized study plan from educational content. Ask the user for subject area, their current knowledge level (beginner/intermediate/advanced), hours per day they can study, number of days for the plan, and their specific learning goals.",
            "schema": {
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "subject_area": {"type": "string"},
                    "knowledge_level": {"type": "string"},
                    "hours_per_day": {"type": "integer"},
                    "days_until_deadline": {"type": "integer"},
                    "learning_goals": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                },
                "required": ["content", "subject_area", "knowledge_level", "hours_per_day", "days_until_deadline", "learning_goals"],
            },
        },
        "build_visual": {
            "endpoint": "/api/v1/visuals/",
            "description": "Create flowchart visual representations from educational content. Ask the user for subject area and confirm they want a flowchart.",
            "schema": {
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "subject_area": {"type": "string"},
                    "visual_type": {"type": "string"},
                },
                "required": ["content", "subject_area", "visual_type"],
            },
        }
    }

    @classmethod
    def get_tool(cls, tool_name: str) -> Dict[str, Any]:
        """Get tool configuration by name."""
        app_logger.log_debug(f"[ToolRegistry] Getting tool configuration for: {tool_name}")
        try:
            tool = cls.TOOLS.get(tool_name, {})
            if tool:
                app_logger.log_debug(f"[ToolRegistry] Successfully retrieved tool configuration for: {tool_name}")
            else:
                app_logger.log_warning(f"[ToolRegistry] Tool not found: {tool_name}")
            return tool
        except Exception as e:
            app_logger.log_error(f"[ToolRegistry] Error in get_tool: {str(e)}")
            return {}

    @classmethod
    def get_all_tools(cls) -> Dict[str, Dict[str, Any]]:
        """Get all registered tools."""
        app_logger.log_debug("[ToolRegistry] Getting all registered tools")
        try:
            tools = cls.TOOLS.copy()
            app_logger.log_debug(f"[ToolRegistry] Successfully retrieved {len(tools)} registered tools")
            return tools
        except Exception as e:
            app_logger.log_error(f"[ToolRegistry] Error in get_all_tools: {str(e)}")
            return {}

    @classmethod
    def get_tools_payload(cls) -> List[Dict[str, Any]]:
        """Generate OpenAI tools payload for function calling."""
        app_logger.log_debug("[ToolRegistry] Generating OpenAI tools payload")
        try:
            payload = [
                {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": spec.get("description", f"Call the {name} service."),
                        "parameters": spec["schema"],
                    },
                }
                for name, spec in cls.TOOLS.items()
            ]
            app_logger.log_debug(f"[ToolRegistry] Successfully generated payload with {len(payload)} tools")
            return payload
        except Exception as e:
            app_logger.log_error(f"[ToolRegistry] Error in get_tools_payload: {str(e)}")
            return []

    @classmethod
    def is_in_process_tool(cls, tool_name: str) -> bool:
        """Check if a tool is handled in-process (not via HTTP)."""
        app_logger.log_debug(f"[ToolRegistry] Checking if tool is in-process: {tool_name}")
        try:
            tool = cls.get_tool(tool_name)
            is_in_process = tool.get("in_process", False)
            app_logger.log_debug(f"[ToolRegistry] Tool {tool_name} is_in_process: {is_in_process}")
            return is_in_process
        except Exception as e:
            app_logger.log_error(f"[ToolRegistry] Error in is_in_process_tool: {str(e)}")
            return False

    @classmethod
    def get_required_fields(cls, tool_name: str) -> List[str]:
        """Get required fields for a tool."""
        app_logger.log_debug(f"[ToolRegistry] Getting required fields for tool: {tool_name}")
        try:
            tool = cls.get_tool(tool_name)
            required_fields = tool.get("schema", {}).get("required", [])
            app_logger.log_debug(f"[ToolRegistry] Tool {tool_name} has {len(required_fields)} required fields: {required_fields}")
            return required_fields
        except Exception as e:
            app_logger.log_error(f"[ToolRegistry] Error in get_required_fields: {str(e)}")
            return []

    @classmethod
    def get_tool_properties(cls, tool_name: str) -> Dict[str, Any]:
        """Get tool schema properties."""
        app_logger.log_debug(f"[ToolRegistry] Getting properties for tool: {tool_name}")
        try:
            tool = cls.get_tool(tool_name)
            properties = tool.get("schema", {}).get("properties", {})
            app_logger.log_debug(f"[ToolRegistry] Tool {tool_name} has {len(properties)} properties")
            return properties
        except Exception as e:
            app_logger.log_error(f"[ToolRegistry] Error in get_tool_properties: {str(e)}")
            return {}

    @classmethod
    def validate_tool_args(cls, tool_name: str, args: Dict[str, Any]) -> List[str]:
        """Validate tool arguments and return missing required fields."""
        app_logger.log_info(f"[ToolRegistry] Validating arguments for tool: {tool_name}")
        try:
            required_fields = cls.get_required_fields(tool_name)
            missing_fields = [f for f in required_fields if f not in args or not args[f]]
            if missing_fields:
                app_logger.log_warning(f"[ToolRegistry] Tool {tool_name} missing required fields: {missing_fields}")
            else:
                app_logger.log_debug(f"[ToolRegistry] All required fields provided for tool: {tool_name}")
            return missing_fields
        except Exception as e:
            app_logger.log_error(f"[ToolRegistry] Error in validate_tool_args: {str(e)}")
            return []
    
    @classmethod
    def get_important_fields(cls, tool_name: str) -> List[str]:
        """Get fields that should always be explicitly provided (no defaults)."""
        app_logger.log_debug(f"[ToolRegistry] Getting important fields for tool: {tool_name}")
        try:
            # Since we removed all defaults and made fields required, this is now handled by required validation
            # But keeping this for any additional validation logic in the future
            important_fields = {
                "generate_flashcards": [],  # All handled by required fields now
                "generate_mcq_set": [],     # All handled by required fields now
                "study_plan": [],           # All handled by required fields now
                "explain_concept": [],      # All handled by required fields now
                "topic_breakdown": [],      # All handled by required fields now
                "extract_key_concepts": [], # All handled by required fields now
                "document_query": [],       # Query is the main requirement
                "generate_question_paper": [], # All handled by required fields now
                "build_visual": []          # All handled by required fields now
            }
            fields = important_fields.get(tool_name, [])
            app_logger.log_debug(f"[ToolRegistry] Tool {tool_name} has {len(fields)} important fields")
            return fields
        except Exception as e:
            app_logger.log_error(f"[ToolRegistry] Error in get_important_fields: {str(e)}")
            return []
    
    @classmethod
    def validate_important_fields(cls, tool_name: str, args: Dict[str, Any]) -> List[str]:
        """Validate that important fields are explicitly provided."""
        app_logger.log_debug(f"[ToolRegistry] Validating important fields for tool: {tool_name}")
        try:
            important_fields = cls.get_important_fields(tool_name)
            missing_important = [f for f in important_fields if f not in args or args[f] is None]
            if missing_important:
                app_logger.log_warning(f"[ToolRegistry] Tool {tool_name} missing important fields: {missing_important}")
            else:
                app_logger.log_debug(f"[ToolRegistry] All important fields provided for tool: {tool_name}")
            return missing_important
        except Exception as e:
            app_logger.log_error(f"[ToolRegistry] Error in validate_important_fields: {str(e)}")
            return []

    @classmethod
    def register_tool(cls, name: str, config: Dict[str, Any]) -> None:
        """Register a new tool."""
        app_logger.log_info(f"[ToolRegistry] Registering new tool: {name}")
        try:
            cls.TOOLS[name] = config
            app_logger.log_info(f"[ToolRegistry] Successfully registered tool: {name}")
        except Exception as e:
            app_logger.log_error(f"[ToolRegistry] Error registering tool {name}: {str(e)}")
            raise

    @classmethod
    def get_content_tools(cls) -> List[str]:
        """Get list of tools that work with document content."""
        app_logger.log_debug("[ToolRegistry] Getting content tools list")
        try:
            content_tools = ["document_query", "generate_flashcards", "topic_breakdown", "explain_concept", "extract_key_concepts",
                            "generate_mcq_set", "generate_question_paper", "study_plan", "build_visual"]
            app_logger.log_debug(f"[ToolRegistry] Successfully retrieved {len(content_tools)} content tools")
            return content_tools
        except Exception as e:
            app_logger.log_error(f"[ToolRegistry] Error in get_content_tools: {str(e)}")
            return []