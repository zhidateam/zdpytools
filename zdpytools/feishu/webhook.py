import httpx
import traceback
from ..utils.log import logger

async def send_wehbook(content, msg_type="plain_text", url: str = "https://open.feishu.cn/open-apis/bot/v2/hook/2fbdfa55-5353-4521-817e-d2efdd6ada02"):
    if not url:
        logger.error(f"send_wehbook url is None")
        return None
    data = {
        "msg_type": msg_type,
        "content": content
    }
    if msg_type == "plain_text":
        data["msg_type"] = "text"
        data["content"] = {"text": content}
    logger.debug(f"send_wehbook url: {url}  data: {data}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data)
            if response.status_code != 200:
                logger.error(f"send_wehbook error: {response.status_code} | {response.text}")
                return False, response
            return True, response
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"send_wehbook error: {e} | {tb}")
        return False, e