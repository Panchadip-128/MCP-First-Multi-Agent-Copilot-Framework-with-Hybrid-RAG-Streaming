"""
Code Indexer - Parses and chunks code files for RAG memory.
"""
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from loguru import logger
import ast
from dataclasses import dataclass


@dataclass
class CodeChunk:
    """Represents a chunk of code."""
    content: str
    file_path: str
    language: str
    start_line: int
    end_line: int
    chunk_type: str  # function, class, import, comment, code
    name: Optional[str] = None


class CodeIndexer:
    """
    Indexes code files into semantic chunks for RAG.
    Supports AST-based chunking for Python and basic chunking for other languages.
    """
    
    SUPPORTED_EXTENSIONS = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'javascript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.cpp': 'cpp',
        '.c': 'c',
        '.go': 'go',
        '.rs': 'rust',
        '.rb': 'ruby',
        '.php': 'php',
        '.md': 'markdown',
        '.txt': 'text',
    }
    
    def __init__(self, max_chunk_size: int = 1000):
        self.max_chunk_size = max_chunk_size
        logger.info(f"Code Indexer created (max_chunk_size={max_chunk_size})")
    
    def index_directory(
        self,
        directory: str,
        project_id: str,
        extensions: Optional[List[str]] = None
    ) -> List[CodeChunk]:
        """
        Index all supported code files in a directory.
        
        Args:
            directory: Path to directory to index
            project_id: Project identifier
            extensions: Optional list of extensions to filter (e.g. ['.py', '.js'])
        
        Returns:
            List of code chunks
        """
        directory_path = Path(directory)
        if not directory_path.exists():
            raise ValueError(f"Directory does not exist: {directory}")
        
        chunks = []
        extensions_to_index = extensions or list(self.SUPPORTED_EXTENSIONS.keys())
        
        # Walk through directory
        for file_path in directory_path.rglob('*'):
            if not file_path.is_file():
                continue
            
            # Skip hidden files and common ignore patterns
            if any(part.startswith('.') for part in file_path.parts):
                continue
            if any(ignore in str(file_path) for ignore in ['node_modules', '__pycache__', 'venv', '.git']):
                continue
            
            # Check extension
            if file_path.suffix not in extensions_to_index:
                continue
            
            try:
                file_chunks = self.index_file(str(file_path), project_id)
                chunks.extend(file_chunks)
                logger.debug(f"Indexed {len(file_chunks)} chunks from {file_path}")
            except Exception as e:
                logger.warning(f"Failed to index {file_path}: {e}")
        
        logger.info(f"Indexed {len(chunks)} total chunks from {directory}")
        return chunks
    
    def index_file(self, file_path: str, project_id: str) -> List[CodeChunk]:
        """
        Index a single file.
        
        Args:
            file_path: Path to file
            project_id: Project identifier
        
        Returns:
            List of code chunks
        """
        path = Path(file_path)
        language = self.SUPPORTED_EXTENSIONS.get(path.suffix, 'unknown')
        
        # Read file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        
        # Use AST-based chunking for Python
        if language == 'python':
            return self._chunk_python_ast(content, file_path, project_id)
        else:
            return self._chunk_basic(content, file_path, language, project_id)
    
    def _chunk_python_ast(
        self,
        content: str,
        file_path: str,
        project_id: str
    ) -> List[CodeChunk]:
        """Chunk Python code using AST."""
        chunks = []
        
        try:
            tree = ast.parse(content)
            lines = content.split('\n')
            
            for node in ast.walk(tree):
                # Extract functions
                if isinstance(node, ast.FunctionDef):
                    start_line = node.lineno
                    end_line = node.end_lineno or start_line
                    chunk_content = '\n'.join(lines[start_line-1:end_line])
                    
                    chunks.append(CodeChunk(
                        content=chunk_content,
                        file_path=file_path,
                        language='python',
                        start_line=start_line,
                        end_line=end_line,
                        chunk_type='function',
                        name=node.name
                    ))
                
                # Extract classes
                elif isinstance(node, ast.ClassDef):
                    start_line = node.lineno
                    end_line = node.end_lineno or start_line
                    chunk_content = '\n'.join(lines[start_line-1:end_line])
                    
                    chunks.append(CodeChunk(
                        content=chunk_content,
                        file_path=file_path,
                        language='python',
                        start_line=start_line,
                        end_line=end_line,
                        chunk_type='class',
                        name=node.name
                    ))
        
        except SyntaxError:
            # Fallback to basic chunking if AST fails
            logger.warning(f"AST parsing failed for {file_path}, using basic chunking")
            return self._chunk_basic(content, file_path, 'python', project_id)
        
        # If no AST chunks found, use basic chunking
        if not chunks:
            return self._chunk_basic(content, file_path, 'python', project_id)
        
        return chunks
    
    def _chunk_basic(
        self,
        content: str,
        file_path: str,
        language: str,
        project_id: str
    ) -> List[CodeChunk]:
        """Basic line-based chunking."""
        chunks = []
        lines = content.split('\n')
        
        # Chunk by max_chunk_size lines
        chunk_lines = []
        start_line = 1
        
        for i, line in enumerate(lines, 1):
            chunk_lines.append(line)
            
            # Create chunk if we hit max size or end of file
            if len('\n'.join(chunk_lines)) >= self.max_chunk_size or i == len(lines):
                if chunk_lines:  # Skip empty chunks
                    chunk_content = '\n'.join(chunk_lines)
                    chunks.append(CodeChunk(
                        content=chunk_content,
                        file_path=file_path,
                        language=language,
                        start_line=start_line,
                        end_line=i,
                        chunk_type='code'
                    ))
                    chunk_lines = []
                    start_line = i + 1
        
        return chunks
