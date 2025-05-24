#!/usr/bin/env python3
"""
CLI entry point for the FakeAI OpenAI compatible server.
"""
#  SPDX-License-Identifier: Apache-2.0

import sys
import uvicorn

from fakeai.config import AppConfig
            

def main():
    """Run the FakeAI server"""
    module_path = "fakeai.app:app"
    # Load the configuration
    config = AppConfig()
    
    # Run the server
    print(f"Starting FakeAI server at http://{config.host}:{config.port}")
    print(f"API documentation available at http://{config.host}:{config.port}/docs")
    
    uvicorn.run(
        module_path,
        host=config.host,
        port=config.port,
        reload=config.debug,
        log_level="info" if not config.debug else "debug",
    )

if __name__ == "__main__":
    sys.exit(main())
