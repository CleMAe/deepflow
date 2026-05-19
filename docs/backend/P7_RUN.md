# P7 Data API — 本地运行

目录结构：`src/app/`（应用）+ `src/shared/`（Protocol，与 P1 冻结一致）。

```bash
cd deepflow
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
set PYTHONPATH=src
uvicorn app.main:app --reload --port 8000
```

- Swagger: http://127.0.0.1:8000/docs
- Demo project: `11111111-1111-1111-1111-111111111111`
