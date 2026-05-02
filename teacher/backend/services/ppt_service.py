from __future__ import annotations

import base64
import hashlib
import hmac
import os
import time
from typing import Dict, Optional

import httpx


DEFAULT_PPT_BASE_URL = "https://zwapi.xfyun.cn"


def validate_ppt_config(config: Dict[str, str]) -> None:
    required = ["XFYUN_PPT_APP_ID", "XFYUN_PPT_API_SECRET"]
    missing = [key for key in required if not config.get(key)]
    if missing:
        raise ValueError("Missing iFlytek PPT config: " + ", ".join(missing))


def load_ppt_config() -> Dict[str, str]:
    return {
        "XFYUN_PPT_APP_ID": os.getenv("XFYUN_PPT_APP_ID", ""),
        "XFYUN_PPT_API_SECRET": os.getenv("XFYUN_PPT_API_SECRET", ""),
        "XFYUN_PPT_BASE_URL": os.getenv("XFYUN_PPT_BASE_URL", DEFAULT_PPT_BASE_URL),
    }


def build_ppt_signature(app_id: str, secret: str, timestamp: int) -> str:
    md5_text = hashlib.md5(f"{app_id}{timestamp}".encode("utf-8")).hexdigest()
    digest = hmac.new(secret.encode("utf-8"), md5_text.encode("utf-8"), hashlib.sha1).digest()
    return base64.b64encode(digest).decode("utf-8")


class XfyunPptClient:
    def __init__(
        self,
        app_id: str,
        api_secret: str,
        base_url: str = DEFAULT_PPT_BASE_URL,
    ):
        self.app_id = app_id
        self.api_secret = api_secret
        self.base_url = base_url.rstrip("/")

    @classmethod
    def from_env(cls) -> "XfyunPptClient":
        config = load_ppt_config()
        validate_ppt_config(config)
        return cls(
            app_id=config["XFYUN_PPT_APP_ID"],
            api_secret=config["XFYUN_PPT_API_SECRET"],
            base_url=config["XFYUN_PPT_BASE_URL"] or DEFAULT_PPT_BASE_URL,
        )

    def _headers(self) -> Dict[str, str]:
        timestamp = int(time.time())
        return {
            "appId": self.app_id,
            "timestamp": str(timestamp),
            "signature": build_ppt_signature(self.app_id, self.api_secret, timestamp),
        }

    async def create_ppt(
        self,
        query: str,
        template_id: str = "",
        author: str = "教学智能体",
        search: bool = False,
        is_card_note: bool = False,
        is_figure: bool = True,
        ai_image: str = "advanced",
    ) -> Dict[str, object]:
        data = {
            "query": query,
            "author": author,
            "search": str(search).lower(),
            "isCardNote": str(is_card_note).lower(),
            "isFigure": str(is_figure).lower(),
            "aiImage": ai_image,
            "language": "cn",
        }
        if template_id:
            data["templateId"] = template_id
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self.base_url}/api/ppt/v2/create",
                headers=self._headers(),
                data=data,
            )
            response.raise_for_status()
            payload = response.json()
        if not payload.get("flag"):
            raise ValueError(payload.get("desc") or "讯飞 PPT 创建失败")
        return payload.get("data", {})

    async def get_progress(self, sid: str) -> Dict[str, object]:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(
                f"{self.base_url}/api/ppt/v2/progress",
                headers=self._headers(),
                params={"sid": sid},
            )
            response.raise_for_status()
            payload = response.json()
        if not payload.get("flag"):
            raise ValueError(payload.get("desc") or "讯飞 PPT 进度查询失败")
        return payload.get("data", {})


async def submit_ppt_task(prompt: str, template_id: str = "") -> Dict[str, object]:
    client = XfyunPptClient.from_env()
    data = await client.create_ppt(prompt, template_id=template_id)
    return {
        "sid": data.get("sid", ""),
        "status": "building",
        "cover_image": data.get("coverImgSrc", ""),
        "title": data.get("title", ""),
        "subtitle": data.get("subTitle", ""),
        "download_url": "",
    }


async def fetch_ppt_status(sid: str) -> Dict[str, object]:
    client = XfyunPptClient.from_env()
    data = await client.get_progress(sid)
    status = data.get("pptStatus", "building")
    return {
        "sid": sid,
        "status": status,
        "progress_text": f"{data.get('donePages', 0)}/{data.get('totalPages', 0)} 页",
        "download_url": data.get("pptUrl", "") or "",
        "error_message": data.get("errMsg", "") or "",
        "total_pages": data.get("totalPages", 0) or 0,
        "done_pages": data.get("donePages", 0) or 0,
    }
