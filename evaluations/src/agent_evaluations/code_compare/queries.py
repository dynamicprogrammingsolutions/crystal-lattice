from __future__ import annotations

FUNCTION_QUERY = {
    "cpp": "[(template_declaration) (function_definition declarator: (function_declarator declarator: (identifier)))] @fdef",
    "java": "(method_declaration name: (_)) @fdef",
    "go": "(function_declaration name: (_)) @fdef",
    "rust": "(function_item name: (_)) @fdef",
    "typescript": "(function_declaration name: (_)) @fdef",
}

COMMENT_QUERIES = {
    "cpp": ["(comment) @comment"],
    "java": ["(line_comment) @comment", "(block_comment) @comment"],
    "go": ["(comment) @comment"],
    "rust": ["(line_comment) @comment", "(block_comment) @comment"],
    "typescript": ["(comment) @comment"],
}