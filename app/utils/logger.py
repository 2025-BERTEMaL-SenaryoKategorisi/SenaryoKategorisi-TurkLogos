"""
Logging configuration
"""
from loguru import logger
import sys
from ..core.config import settings

def setup_logging():
    """Setup logging configuration."""
    
    # Remove default handler
    logger.remove()
    
    # Add custom handler
    logger.add(
        sys.stdout,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
               "<level>{message}</level>",
        colorize=True
    )
    
    # Add file handler for production
    if settings.environment == "production":
        logger.add(
            "logs/turklogos_agent.log",
            rotation="1 day",
            retention="30 days",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}"
        )
    
    return logger