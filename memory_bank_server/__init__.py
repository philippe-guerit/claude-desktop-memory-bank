from . import server

__all__ = ["server"]

def main():
    """Main entry point for the package."""
    import asyncio
    asyncio.run(server.main())
