from typing import Generator

def get_db() -> Generator:
    try:
        # Mocking the session for now until SQLAlchemy is fully configured
        class MockSession:
            def execute(self, query):
                pass
        yield MockSession()
    finally:
        pass
