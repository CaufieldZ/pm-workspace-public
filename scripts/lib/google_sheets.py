"""Google Sheets API 薄封装（Service Account）。

依赖：google-auth + google-api-python-client（pip install --user google-auth google-api-python-client）

凭据约定：~/.config/gcloud/pm-sheet-sa.json（chmod 600）

代理：httplib2 / urllib 自动读 HTTPS_PROXY / ALL_PROXY 等环境变量，脚本不注入代理。
"""

from __future__ import annotations

from pathlib import Path

DEFAULT_CREDS = Path.home() / ".config" / "gcloud" / "pm-sheet-sa.json"
SCOPES_RW = ["https://www.googleapis.com/auth/spreadsheets"]
SCOPES_RO = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def get_service(creds_path: Path | str | None = None, *, write: bool = False):
    """返回 Sheets v4 service。write=True 走读写 scope，否则只读。"""
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    creds_path = Path(creds_path) if creds_path else DEFAULT_CREDS
    if not creds_path.exists():
        raise FileNotFoundError(
            f"Service account credentials 不存在：{creds_path}\n"
            f"  → 从 GCP Console → IAM → 服务账号 → 密钥 下载 JSON 放到此路径"
        )
    creds = service_account.Credentials.from_service_account_file(
        str(creds_path), scopes=SCOPES_RW if write else SCOPES_RO
    )
    return build("sheets", "v4", credentials=creds, cache_discovery=False)


def read_range(svc, sheet_id: str, range_name: str) -> list[list[str]]:
    """读 range，返回二维列表。range_name 如 '增长需求池!A1:N1200'。"""
    resp = svc.spreadsheets().values().get(
        spreadsheetId=sheet_id, range=range_name,
        valueRenderOption="UNFORMATTED_VALUE",
        dateTimeRenderOption="FORMATTED_STRING",
    ).execute()
    return resp.get("values", [])


def read_tab(svc, sheet_id: str, tab_title: str) -> list[list[str]]:
    """读整个 tab（自动确定范围）。"""
    return read_range(svc, sheet_id, f"'{tab_title}'")


def update_cells(svc, sheet_id: str, range_name: str, values: list[list]) -> dict:
    """批量写 range。values 是二维列表，shape 应匹配 range。

    范围示例 'tab!L5'（单元格）/ 'tab!L5:L10'（一列多行）。
    """
    body = {"values": values}
    return svc.spreadsheets().values().update(
        spreadsheetId=sheet_id, range=range_name, valueInputOption="USER_ENTERED", body=body,
    ).execute()


def append_row(svc, sheet_id: str, tab_title: str, row: list) -> dict:
    """末尾追加一行。"""
    body = {"values": [row]}
    return svc.spreadsheets().values().append(
        spreadsheetId=sheet_id, range=f"'{tab_title}'", valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS", body=body,
    ).execute()


# 列号工具：1 → A，27 → AA
def col_letter(n: int) -> str:
    """1-based 列号转字母。1=A, 26=Z, 27=AA。"""
    if n < 1:
        raise ValueError(f"col_letter: n={n} 必须 >= 1")
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s
