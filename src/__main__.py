from src import app

import uvicorn

uvicorn.run(
    'src.app:app',
    reload=True,
    host='0.0.0.0',
    workers=1
)
