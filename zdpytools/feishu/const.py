# 常量定义
FEISHU_HOST = "https://open.feishu.cn"


TENANT_ACCESS_TOKEN_URI = "/open-apis/auth/v3/tenant_access_token/internal"
# 新增记录https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-record/create
BITABLE_RECORDS = "/open-apis/bitable/v1/apps/:app_token/tables/:table_id/records"

# 查询记录文档：https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/bitable-v1/app-table-record/search
BITABLE_RECORDS_SEARCH = "/open-apis/bitable/v1/apps/:app_token/tables/:table_id/records/search"
BITABLE_RECORD = "/open-apis/bitable/v1/apps/:app_token/tables/:table_id/records/:record_id"

# 批量获取记录 https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/bitable-v1/app-table-record/batch_get
BATCH_RECORDS = "https://open.feishu.cn/open-apis/bitable/v1/apps/:app_token/tables/:table_id/records/batch_get"


# 列出,更新字段 https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-field/update
TABLES_FIELDS = '/open-apis/bitable/v1/apps/:app_token/tables/:table_id/fields/:field_id'

# 获取素材临时下载链接 https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/drive-v1/media/batch_get_tmp_download_url
BATCH_GET_TMP_DOWNLOAD_URL = '/open-apis/drive/v1/medias/batch_get_tmp_download_url'

# 上传素材 https://open.feishu.cn/document/server-docs/docs/drive-v1/media/upload_all
UPLOAD_MEDIA_URI = '/open-apis/drive/v1/medias/upload_all'

# 复制多维表格 https://open.feishu.cn/document/server-docs/docs/bitable-v1/app/copy
BITABLE_COPY_URI = '/open-apis/bitable/v1/apps/:app_token/copy'

# 批量添加协作者权限 https://open.feishu.cn/document/server-docs/docs/drive-v1/permission/members/batch_create
BATCH_CREATE_PERMISSIONS_URI = '/open-apis/drive/v1/permissions/:token/members/batch_create'

# 转移所有者权限 https://open.feishu.cn/document/server-docs/docs/drive-v1/permission/members/transfer_owner
TRANSFER_OWNER_URI = '/open-apis/drive/v1/permissions/:token/members/transfer_owner'

# 列出数据表 https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table/list
BITABLE_TABLES_LIST_URI = '/open-apis/bitable/v1/apps/:app_token/tables'
