# PDF2md-CLI 架构设计与技术方案

**版本**: 1.0
**日期**: 2026-01-06
**状态**: 草稿
**作者**: 项目团队

## 目录

1. [系统概述](#1-系统概述)
2. [架构原则](#2-架构原则)
3. [系统架构](#3-系统架构)
4. [组件设计](#4-组件设计)
5. [数据流](#5-数据流)
6. [API 设计](#6-api-设计)
7. [数据模型](#7-数据模型)
8. [错误处理策略](#8-错误处理策略)
9. [安全设计](#9-安全设计)
10. [技术栈](#10-技术栈)
11. [部署架构](#11-部署架构)
12. [性能考虑](#12-性能考虑)
13. [测试策略](#13-测试策略)

---

## 1. 系统概述

### 1.1 目标

PDF2md-CLI 是一个客户端-服务器工具，使用远程 GPU 服务器将 PDF 文件转换为 Markdown 格式。系统专为目标内部网络部署而设计，专注于简洁性、鲁棒性和可维护性。

### 1.2 核心需求

**功能需求**（来自 spec.md）：
- FR-001 至 FR-027：完整的功能集
- 支持单文件转换（MVP）
- 处理最大 500MB 的文件
- 在 30 秒内转换 10 页 PDF
- 支持 10 个并发请求
- 提供清晰的错误消息

**非功能需求**：
- **鲁棒性**：处理网络故障、转换错误、超时
- **可读性**：遵循 Python 规范（PEP 8）、自文档化代码
- **可维护性**：模块化设计、SOLID 原则、DRY 合规
- **复杂度控制**：无过度设计、YAGNI 合规

### 1.3 范围和边界

**范围内（MVP）**：
- 单文件 PDF 到 Markdown 转换
- 内部网络部署
- 配置文件管理
- 基本错误处理和重试
- 进度指示
- 临时文件清理

**范围外（未来）**：
- 批量转换（US3）
- 递归目录处理（US3）
- 认证/授权
- Web UI
- 转换历史/队列管理

---

## 2. 架构原则

架构遵循项目宪法的核心原则：

### 2.1 SOLID 原则

**单一职责原则（SRP）**：
- 每个模块只有一个变更原因
- 客户端仅处理 CLI 和 HTTP 通信
- 服务端仅处理转换和文件管理

**开闭原则（OCP）**：
- 转换引擎可以替换而无需修改 API
- 新文件格式可以通过扩展添加

**里氏替换原则（LSP）**：
- 任何转换器实现都可以替换
- 文件存储后端可以互换

**接口隔离原则（ISP）**：
- 每个组件的小而专一的接口
- 客户端不依赖未使用的方法

**依赖倒置原则（DIP）**：
- 高层模块依赖抽象
- API 层依赖转换器接口，而非实现

### 2.2 DRY 原则

**无重复**：
- `shared/` 模块中的共享工具
- 通用的异常处理
- 单一的配置管理模块

**抽象而非重复**：
- 上传和下载的通用文件处理程序
- 可重用的 HTTP 客户端包装器

### 2.3 简洁性和反过度设计

**YAGNI（你不需要它）**：
- MVP 使用同步 API（如需要，稍后添加异步作业队列）
- 简单文件存储（无数据库）
- 基本配置（无复杂验证）

**简单胜于聪明**：
- 直截了当的错误处理
- 清晰的函数名
- 最少的抽象层

**无过早优化**：
- 优化前先分析
- 首先专注于可读性
- 仅在测量后优化关键路径

### 2.4 鲁棒性

**显式错误处理**：
- 所有错误路径都显式处理
- 为用户提供清晰的错误消息
- 为调试记录详细日志

**快速且大声地失败**：
- 在边界验证输入
- 立即引发错误
- 不传播无效状态

**优雅降级**：
- 在错误时清理资源
- 提供恢复指导
- 永不留下孤立文件

---

## 3. 系统架构

### 3.1 高层架构

```
┌─────────────────────────────────────────────────────────────┐
│                         客户端机器                           │
│  ┌────────────────────────────────────────────────────┐    │
│  │              CLI 接口 (Typer)                      │    │
│  │  - 解析命令行参数                                   │    │
│  │  - 加载配置                                         │    │
│  │  - 显示进度/错误                                    │    │
│  └─────────────────┬──────────────────────────────────┘    │
│                    │                                         │
│  ┌─────────────────▼──────────────────────────────────┐    │
│  │         HTTP 客户端 (httpx)                         │    │
│  │  - 上传 PDF 并显示进度                              │    │
│  │  - 下载 Markdown                                    │    │
│  │  - 处理网络错误                                     │    │
│  └─────────────────┬──────────────────────────────────┘    │
│                    │                                         │
│  ┌─────────────────▼──────────────────────────────────┐    │
│  │      文件处理程序和验证器                           │    │
│  │  - 上传前验证 PDF                                   │    │
│  │  - 检查文件冲突                                     │    │
│  │  - 将 Markdown 保存到原始路径                       │    │
│  └─────────────────┬──────────────────────────────────┘    │
│                    │                                         │
└────────────────────┼─────────────────────────────────────────┘
                     │
                     │ HTTP/HTTPS
                     │ (Multipart 上传)
                     │
┌────────────────────▼─────────────────────────────────────────┐
│                    服务器 (GPU 机器)                         │
│                     ┌──────────────────────┐                 │
│                     │   FastAPI 应用       │                 │
│                     │   - CORS 处理        │                 │
│                     │   - 请求日志         │                 │
│                     └──────────┬───────────┘                 │
│                                │                              │
│            ┌───────────────────┼───────────────────┐         │
│            │                   │                   │          │
│  ┌─────────▼────────┐  ┌──────▼───────┐  ┌───────▼──────┐  │
│  │  文件验证器      │  │ 文件管理器   │  │  转换器      │  │
│  │  - 类型检查      │  │ - 临时存储   │  │  - Marker    │  │
│  │  - 大小限制      │  │ - 清理       │  │  - GPU OCR   │  │
│  │  - 文件名净化    │  │ - 命名       │  │  - 输出      │  │
│  └──────────────────┘  └──────────────┘  └──────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              GPU 资源 (Marker)                         │  │
│  │  - CUDA 加速                                           │  │
│  │  - OCR 处理                                            │  │
│  │  - 表格/图像提取                                        │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 部署架构

```
内部网络 (192.168.1.0/24)

┌─────────────────┐
│  用户机器       │
│  (客户端)       │
│  192.168.1.10   │
└────────┬────────┘
         │
         │ HTTP 请求
         │
┌────────▼───────────────────────┐
│  服务器 (设备 A)               │
│  192.168.1.100:8000            │
│                                │
│  ┌──────────────────────────┐  │
│  │  Docker 容器（可选）      │  │
│  │  - FastAPI 应用           │  │
│  │  - Marker                │  │
│  │  - GPU 访问              │  │
│  └──────────────────────────┘  │
│                                │
│  GPU: NVIDIA RTX 3080          │
│  存储: /tmp/pdf2md/            │
└────────────────────────────────┘
```

### 3.3 组件交互图

```
用户 → CLI → HTTP 客户端 → [网络] → FastAPI → 文件验证器
                                                          ↓
                                                    文件管理器
                                                          ↓
                                                    转换器 (Marker)
                                                          ↓
                                                    文件管理器 (清理)
                                                          ↓
                                                    FastAPI → [网络] → HTTP 客户端 → 文件处理程序 → 磁盘
```

---

## 4. 组件设计

### 4.1 客户端组件 (`client/`)

#### 4.1.1 CLI 模块 (`cli.py`)

**职责**：解析命令，协调工作流

**关键函数**：
```python
def convert(file_path: Path, output: Optional[Path] = None) -> None:
    """通过远程服务器将 PDF 转换为 Markdown。"""

def config_init(server_url: str) -> None:
    """初始化配置文件。"""

def config_show() -> None:
    """显示当前配置。"""
```

**依赖**：`typer`、`config.py`、`client.py`、`file_handler.py`

**宪章合规性**：
- ✅ SRP：仅处理 CLI，无业务逻辑
- ✅ DRY：重用配置模块

#### 4.1.2 配置模块 (`config.py`)

**职责**：管理配置文件生命周期

**关键函数**：
```python
def load_config() -> ServerConfig:
    """从 ~/.pdf2md/config.json 加载配置。"""

def save_config(config: ServerConfig) -> None:
    """将配置保存到文件。"""

def get_config_path() -> Path:
    """获取特定于平台的配置路径。"""
```

**配置架构**：
```python
class ServerConfig(BaseModel):
    server_url: str = "http://localhost:8000"
    timeout: int = 300
    chunk_size: int = 8192
    max_retries: int = 3
    verify_ssl: bool = True
    output_dir: Optional[Path] = None
    overwrite: bool = False
```

**配置层次结构**（优先级顺序）：
1. 命令行标志（最高）
2. 环境变量（`PDF2MD_SERVER_URL` 等）
3. 配置文件（`~/.pdf2md/config.json`）
4. 硬编码默认值（最低）

#### 4.1.3 HTTP 客户端模块 (`client.py`)

**职责**：与服务器的网络通信

**关键函数**：
```python
async def upload_pdf(pdf_path: Path, config: ServerConfig) -> ConversionResult:
    """上传 PDF 并下载转换后的 Markdown。"""

class PDF2MDClient:
    async def convert(self, pdf_path: Path) -> Path:
        """将 PDF 转换为 Markdown。"""

    async def _upload_with_progress(self, file: Path) -> None:
        """使用进度条上传文件。"""

    async def _download_with_progress(self) -> Path:
        """使用进度条下载结果。"""
```

**错误处理**：
- 网络错误：使用指数退避重试（最多 3 次）
- 服务器错误：不重试，记录并退出
- 超时：每个请求可配置

**进度指示**：
- 上传：`tqdm` 显示传输的字节数
- 下载：`tqdm` 显示接收的字节数
- 转换：服务器端进度（如果可用）

#### 4.1.4 文件处理程序模块 (`file_handler.py`)

**职责**：客户端文件操作和验证

**关键函数**：
```python
def validate_pdf_file(file_path: Path) -> None:
    """验证 PDF 存在、可读、在大小限制内。"""

def check_output_conflict(output_path: Path, overwrite: bool) -> None:
    """检查输出文件是否存在，提示或引发。"""

def save_markdown(content: str, output_path: Path) -> None:
    """将 Markdown 内容保存到文件。"""
```

**验证检查**：
- 文件存在：`Path.exists()`
- 文件可读：`Path.stat().st_size > 0`
- 文件类型：魔术字节（开头为 `%PDF`）
- 大小限制：`Path.stat().st_size <= 500 * 1024 * 1024`

#### 4.1.5 异常模块 (`exceptions.py`)

**自定义异常**：
```python
class PDF2MDClientError(Exception): pass
class ConfigError(PDF2MDClientError): pass
class FileNotFoundError(ConfigError): pass
class ValidationError(PDF2MDClientError): pass
class NetworkError(PDF2MDClientError): pass
class ConversionError(PDF2MDClientError): pass
```

### 4.2 服务器组件 (`server/`)

#### 4.2.1 FastAPI 应用 (`main.py`)

**职责**：HTTP 服务器和请求路由

**关键配置**：
```python
app = FastAPI(
    title="PDF2MD 转换服务",
    version="1.0.0",
    description="使用 GPU 加速将 PDF 文件转换为 Markdown"
)

# 中间件
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 仅内部网络
    allow_methods=["POST"],
    allow_headers=["*"]
)
```

**启动/关闭**：
```python
@app.on_event("startup")
async def startup_event():
    """初始化转换器并清理临时目录。"""
    logger.info("启动 PDF2MD 服务器...")
    cleanup_temp_directory()

@app.on_event("shutdown")
async def shutdown_event():
    """清理资源。"""
    logger.info("关闭 PDF2MD 服务器...")
    cleanup_temp_directory()
```

#### 4.2.2 API 模块 (`api/convert.py`)

**职责**：HTTP 端点处理

**端点**：
```python
@app.post("/convert")
async def convert_pdf(
    file: UploadFile,
    response: Response
) -> FileResponse:
    """
    将 PDF 转换为 Markdown。

    - **file**: PDF 文件 (multipart/form-data)
    - **returns**: Markdown 文件 (application/octet-stream)
    - **raises**: 400 表示无效输入，500 表示转换错误
    """
```

**请求流程**：
1. 验证文件类型和大小
2. 保存到临时位置
3. 调用转换器
4. 将结果流式传输回客户端
5. 清理临时文件

#### 4.2.3 转换器模块 (`core/converter.py`)

**职责**：使用 Marker 进行 PDF 到 Markdown 的转换

**关键接口**：
```python
class PDFConverter(ABC):
    @abstractmethod
    async def convert(self, pdf_path: Path, output_path: Path) -> None:
        """将 PDF 转换为 Markdown。"""

class MarkerConverter(PDFConverter):
    async def convert(self, pdf_path: Path, output_path: Path) -> None:
        """使用 Marker 库进行 GPU 加速转换。"""
        # Marker 集成
        from marker.convert import convert_single_pdf

        convert_single_pdf(
            str(pdf_path),
            str(output_path),
            max_pages=None,  # 无限制
            ocr_all_pages=True  # 使用 GPU OCR
        )
```

**错误处理**：
- 捕获 Marker 异常并包装为 `ConversionError`
- 记录详细错误以供调试
- 提供用户友好的错误消息

#### 4.2.4 文件管理器模块 (`core/file_manager.py`)

**职责**：临时文件存储和清理

**关键函数**：
```python
class TempFileManager:
    def __init__(self, base_dir: Path = Path("/tmp/pdf2md")):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def save_upload(self, upload_file: UploadFile) -> Path:
        """将上传的文件保存到具有唯一名称的临时位置。"""
        file_id = uuid4()
        temp_path = self.base_dir / f"{file_id}_{upload_file.filename}"

        async with aiofiles.open(temp_path, "wb") as f:
            while content := await upload_file.read(8192):
                await f.write(content)

        return temp_path

    async def cleanup(self, *paths: Path) -> None:
        """删除临时文件。"""
        for path in paths:
            try:
                path.unlink(missing_ok=True)
            except Exception as e:
                logger.warning(f"清理失败 {path}: {e}")

    def cleanup_all(self) -> None:
        """删除临时目录中的所有文件。"""
        for file in self.base_dir.glob("*"):
            file.unlink(missing_ok=True)
```

**命名策略**：
- 使用 UUID 防止冲突
- 格式：`{uuid}_{original_filename}`
- 示例：`a1b2c3d4-document.pdf`

#### 4.2.5 文件验证器模块 (`utils/validation.py`)

**职责**：服务器端输入验证

**关键函数**：
```python
async def validate_upload(
    file: UploadFile,
    max_size: int = 500 * 1024 * 1024
) -> None:
    """验证上传的文件。"""
    # 检查文件类型
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "仅支持 PDF 文件")

    # 检查文件大小（读取第一个块）
    first_chunk = await file.read(8192)
    await file.seek(0)  # 重置以供重新读取

    if not first_chunk.startswith(b"%PDF"):
        raise HTTPException(400, "无效的 PDF 文件")

    # 净化文件名
    safe_filename = sanitize_filename(file.filename)
    file.filename = safe_filename

def sanitize_filename(filename: str) -> str:
    """删除路径遍历和危险字符。"""
    # 删除目录路径
    filename = Path(filename).name
    # 删除危险字符
    filename = re.sub(r'[<>:"|?*]', '_', filename)
    return filename
```

#### 4.2.6 模型模块 (`models/requests.py`)

**职责**：Pydantic 模式用于验证

**模式**：
```python
class ConversionRequest(BaseModel):
    """转换请求模型。"""

class ConversionResponse(BaseModel):
    """成功转换响应模型。"""
    output_filename: str
    pages_processed: int
    conversion_time: float

class ErrorResponse(BaseModel):
    """错误响应模型。"""
    error: str
    detail: str
    troubleshooting: str
```

---

## 5. 数据流

### 5.1 成功转换流程

```
1. 用户运行：pdf2md document.pdf

2. CLI：
   - 从 ~/.pdf2md/config.json 加载配置
   - 验证 document.pdf 存在且是有效的 PDF
   - 检查 document.md 不存在（或询问是否覆盖）

3. HTTP 客户端：
   - 连接到 server_url (http://192.168.1.100:8000)
   - 使用 multipart/form-data 上传 document.pdf
   - 显示进度条：[################----] 80% 40MB/50MB

4. 服务器：
   - 接收请求
   - 验证文件类型和大小
   - 保存到 /tmp/pdf2md/{uuid}_document.pdf
   - 调用 converter.convert()

5. 转换器 (Marker)：
   - 加载 PDF
   - 提取文本、表格、图像
   - 应用 OCR（GPU 加速）
   - 生成 Markdown
   - 保存到 /tmp/pdf2md/{uuid}_document.md

6. 服务器：
   - 读取 Markdown 文件
   - 使用 Content-Disposition 头流式传输回客户端
   - 清理两个临时文件

7. HTTP 客户端：
   - 使用进度条下载 Markdown
   - 保存到 document.md（原始 PDF 位置）

8. CLI：
   - 显示成功："✓ 转换完成：document.md (42 页, 12.3秒)"
   - 以代码 0 退出
```

### 5.2 错误流程 - 网络故障

```
1. 用户运行：pdf2md document.pdf

2. HTTP 客户端：
   - 尝试连接到服务器
   - 30 秒超时后连接被拒绝

3. HTTP 客户端：
   - 记录错误："连接被拒绝：192.168.1.100:8000"
   - 重试 1：等待 2 秒，再次尝试（失败）
   - 重试 2：等待 4 秒，再次尝试（失败）
   - 重试 3：等待 8 秒，再次尝试（失败）
   - 超过最大重试次数

4. CLI：
   - 显示错误：
     "✗ 网络错误：无法连接到服务器
     服务器：http://192.168.1.100:8000
     故障排除：
     - 检查服务器是否运行：'curl http://192.168.1.100:8000/health'
     - 检查网络连接：'ping 192.168.1.100'
     - 验证配置中的 server_url：'pdf2md config show'"

5. 以代码 1 退出
```

### 5.3 错误流程 - 无效的 PDF

```
1. 用户运行：pdf2md document.txt

2. 文件处理程序（客户端）：
   - 验证文件类型
   - 检查扩展名：.txt（不是 .pdf）
   - 读取魔术字节："Hello world"（不是 "%PDF"）

3. CLI：
   - 显示错误：
     "✗ 无效文件：document.txt
     期望：PDF 文件
     实际：文本文件
     提示：使用 'pdf2md document.pdf' 转换 PDF 文件"

4. 以代码 1 退出
```

---

## 6. API 设计

### 6.1 端点规范

#### POST /convert

将 PDF 文件转换为 Markdown。

**请求**：
```http
POST /convert HTTP/1.1
Host: 192.168.1.100:8000
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="document.pdf"
Content-Type: application/pdf

[PDF 二进制数据]
------WebKitFormBoundary--
```

**成功响应**（200 OK）：
```http
HTTP/1.1 200 OK
Content-Type: text/markdown
Content-Disposition: attachment; filename="document.md"
X-Pages-Processed: 42
X-Conversion-Time: 12.3

# 文档标题

这是转换后的 markdown 内容...
```

**错误响应**：

**400 Bad Request**（无效输入）：
```json
{
  "error": "InvalidRequest",
  "detail": "文件大小超过最大允许大小",
  "troubleshooting": "最大文件大小为 500MB。请将 PDF 拆分为更小的文件。"
}
```

**500 Internal Server Error**（转换失败）：
```json
{
  "error": "ConversionError",
  "detail": "PDF 转换失败：OCR 处理失败",
  "troubleshooting": "查看服务器日志了解详情。PDF 可能已损坏或受密码保护。"
}
```

**503 Service Unavailable**（GPU 过载）：
```json
{
  "error": "ServiceUnavailable",
  "detail": "GPU 资源当前已满负荷",
  "troubleshooting": "几分钟后重试，或联系管理员增加容量。"
}
```

### 6.2 OpenAPI 规范

```yaml
openapi: 3.0.0
info:
  title: PDF2MD 转换服务
  version: 1.0.0
  description: 使用 GPU 加速将 PDF 文件转换为 Markdown

paths:
  /convert:
    post:
      summary: 将 PDF 转换为 Markdown
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                file:
                  type: string
                  format: binary
      responses:
        '200':
          description: 转换成功
          content:
            text/markdown:
              schema:
                type: string
          headers:
            X-Pages-Processed:
              schema:
                type: integer
            X-Conversion-Time:
              schema:
                type: number
        '400':
          description: 无效请求
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '500':
          description: 转换错误
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

components:
  schemas:
    ErrorResponse:
      type: object
      required:
        - error
        - detail
      properties:
        error:
          type: string
        detail:
          type: string
        troubleshooting:
          type: string
```

---

## 7. 数据模型

### 7.1 配置模型

```python
from pydantic import BaseModel, Field
from pathlib import Path

class ServerConfig(BaseModel):
    """存储在 ~/.pdf2md/config.json 中的服务器配置"""

    server_url: str = Field(
        default="http://localhost:8000",
        description="PDF2MD 服务器的 URL"
    )

    timeout: int = Field(
        default=300,
        ge=1,
        le=3600,
        description="请求超时（秒）"
    )

    chunk_size: int = Field(
        default=8192,
        ge=1024,
        le=1048576,
        description="上传/下载块大小（字节）"
    )

    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="网络错误的最大重试次数"
    )

    verify_ssl: bool = Field(
        default=True,
        description="验证 HTTPS 的 SSL 证书"
    )

    output_dir: Path | None = Field(
        default=None,
        description="默认输出目录（null = 与 PDF 相同）"
    )

    overwrite: bool = Field(
        default=False,
        description="覆盖现有 Markdown 文件而不询问"
    )

    class Config:
        json_encoders = {
            Path: str
        }
```

### 7.2 请求/响应模型

```python
from pydantic import BaseModel

class ConversionRequest(BaseModel):
    """转换请求元数据（用于未来的异步版本）"""
    filename: str
    file_size: int
    options: dict = {}

class ConversionResponse(BaseModel):
    """成功转换响应"""
    output_filename: str
    pages_processed: int
    conversion_time: float
    output_size_bytes: int

class ErrorResponse(BaseModel):
    """错误响应"""
    error: str  # 错误代码
    detail: str  # 人类可读的描述
    troubleshooting: str = ""  # 可操作的提示

    class Config:
        schema_extra = {
            "example": {
                "error": "InvalidRequest",
                "detail": "文件大小超过最大允许大小",
                "troubleshooting": "最大文件大小为 500MB。请拆分 PDF。"
            }
        }
```

### 7.3 内部模型

```python
class ConversionJob:
    """转换作业的内部表示"""

    def __init__(
        self,
        job_id: str,
        pdf_path: Path,
        original_filename: str
    ):
        self.job_id = job_id
        self.pdf_path = pdf_path
        self.original_filename = original_filename
        self.md_path = pdf_path.with_suffix(".md")
        self.created_at = datetime.now()
        self.status = "pending"

    def mark_in_progress(self) -> None:
        self.status = "converting"
        self.started_at = datetime.now()

    def mark_completed(self, pages: int) -> None:
        self.status = "completed"
        self.completed_at = datetime.now()
        self.pages_processed = pages
        self.conversion_time = (
            self.completed_at - self.started_at
        ).total_seconds()

    def mark_failed(self, error: str) -> None:
        self.status = "failed"
        self.failed_at = datetime.now()
        self.error = error
```

---

## 8. 错误处理策略

### 8.1 错误分类

**客户端错误（4xx）**：
- `ValidationError`：无效文件类型、大小超限
- `NotFoundError`：未找到配置文件
- `ConflictError`：输出文件已存在

**网络错误**：
- `ConnectionError`：服务器不可达
- `TimeoutError`：请求超时
- `HTTPError`：服务器返回非 2xx 响应

**服务器错误（5xx）**：
- `ConversionError`：PDF 转换失败
- `ResourceError`：GPU 不可用、磁盘已满
- `InternalError`：意外的服务器错误

### 8.2 重试策略

**可重试的错误**：
- 连接被拒绝
- 请求超时
- 服务器不可用（503）

**重试逻辑**：
```python
async def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    base_delay: float = 2.0
) -> Any:
    """使用指数退避重试。"""
    for attempt in range(max_retries + 1):
        try:
            return await func()
        except (ConnectionError, TimeoutError) as e:
            if attempt == max_retries:
                raise
            delay = base_delay * (2 ** attempt)
            logger.warning(f"在 {delay}s 后重试 {attempt + 1}/{max_retries}")
            await asyncio.sleep(delay)
```

**不可重试的错误**：
- 验证错误（4xx）：重试不会改变
- 转换错误（500）：可能是持久的
- 认证错误：没有凭据更改无法成功

### 8.3 错误消息设计

**原则**：
1. **可操作**：告诉用户做什么
2. **具体**：包含相关详细信息（文件名、错误代码）
3. **结构化**：分别的错误、详细信息、故障排除

**模板**：
```
✗ {错误类型}：{具体描述}

{出了什么问题}

故障排除：
- {可操作的提示 1}
- {可操作的提示 2}
- {可操作的提示 3}

文档：https://github.com/user/pdf2md-cli#error-codes
```

**示例**：

**网络错误**：
```
✗ 网络错误：无法连接到服务器

在 3 次尝试后无法连接到 http://192.168.1.100:8000

故障排除：
- 检查服务器是否运行：curl http://192.168.1.100:8000/health
- 检查网络连接：ping 192.168.1.100
- 验证配置中的 server_url：pdf2md config show
- 检查防火墙设置
```

**转换错误**：
```
✗ 转换错误：PDF 处理失败

PDF 无法转换：Marker 处理失败

详细信息：
- 文件：document.pdf (15.2 MB)
- 服务器：http://192.168.1.100:8000
- 错误：CUDA 内存不足

故障排除：
- PDF 可能太大或图像太多
- 先尝试转换较小的文件
- 检查服务器日志了解详情：ssh server 'tail -f /var/log/pdf2md.log'
- 如果问题持续存在，请联系管理员
```

### 8.4 错误时的清理

**保证清理**：
```python
async def convert_with_cleanup(pdf_path: Path) -> Path:
    """转换 PDF，确保即使出错也清理。"""
    temp_files = []

    try:
        # 将上传保存到临时
        temp_pdf = await file_manager.save_upload(pdf_path)
        temp_files.append(temp_pdf)

        # 转换
        temp_md = await converter.convert(temp_pdf)
        temp_files.append(temp_md)

        return temp_md

    except Exception as e:
        # 记录错误以供调试
        logger.error(f"转换失败：{e}", exc_info=True)

        # 引发用户面对的错误
        raise ConversionError(f"转换失败：{e}") from e

    finally:
        # 始终清理
        await file_manager.cleanup(*temp_files)
```

---

## 9. 安全设计

### 9.1 输入验证

**文件类型验证**：
- 检查文件扩展名（`.pdf`）
- 验证魔术字节（`%PDF-`）
- 使用 `python-magic` 库进行可靠检测

**文件大小限制**：
- 客户端：上传前拒绝 > 500MB 的文件
- 服务器：在上传期间强制执行限制
- 流式上传以避免内存耗尽

**文件名净化**：
```python
def sanitize_filename(filename: str) -> str:
    """删除危险字符和路径遍历。"""
    # 删除目录路径
    filename = Path(filename).name

    # 删除危险字符
    filename = re.sub(r'[<>:"|?*\\\x00-\x1f]', '_', filename)

    # 限制长度
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255 - len(ext)] + ext

    # 防止 Unix 上的隐藏文件
    if filename.startswith("."):
        filename = "_" + filename[1:]

    return filename
```

### 9.2 资源限制

**DoS 防护**：
```python
# FastAPI 配置
app = FastAPI()

# 限制请求大小
@app.post("/convert")
async def convert_pdf(
    file: UploadFile = File(max_size=500 * 1024 * 1024)  # 500MB
):
    ...
```

**并发限制**：
```python
from asyncio import Semaphore

# 限制并发转换
conversion_semaphore = Semaphore(10)

@app.post("/convert")
async def convert_pdf(file: UploadFile):
    async with conversion_semaphore:
        # 一次最多 10 个转换
        return await do_conversion(file)
```

**内存限制**：
- 流式文件上传（不要将整个文件加载到内存中）
- 转换后立即清理临时文件
- 监控内存使用，如果 > 80% 则拒绝

### 9.3 文件安全

**临时文件隔离**：
- 使用专用临时目录（`/tmp/pdf2md/`）
- 随机 UUID 文件名防止猜测
- 设置限制性权限：`chmod 600`

**路径遍历防护**：
```python
def safe_path_join(base: Path, filename: str) -> Path:
    """安全连接路径，防止遍历。"""
    # 净化文件名
    safe = sanitize_filename(filename)

    # 连接并解析
    full_path = (base / safe).resolve()

    # 确保结果在基础目录下
    if not str(full_path).startswith(str(base.resolve())):
        raise ValueError("检测到路径遍历")

    return full_path
```

### 9.4 日志安全

**不记录敏感数据**：
- ✅ 日志："正在转换文件：a1b2c3d4-document.pdf"
- ❌ 日志："正在转换文件：/home/user/sensitive-doc.pdf"

**净化错误消息**：
```python
def safe_error_message(error: Exception, file_path: Path) -> str:
    """生成不泄露路径的错误消息。"""
    filename = file_path.name  # 仅文件名，不是完整路径
    return f"处理 {filename} 时出错：{str(error)}"
```

**审计日志**：
```python
logger.info(
    "conversion_requested",
    extra={
        "client_ip": request.client.host,
        "file_size": file_size,
        "filename": sanitized_filename,
        "timestamp": datetime.now().isoformat()
    }
)
```

---

## 10. 技术栈

### 10.1 最终技术选择

**客户端**：
- `typer` - 具有类型提示的现代 CLI 框架
- `httpx` - 异步 HTTP 客户端（支持同步/异步）
- `pydantic` - 数据验证和设置管理
- `tqdm` - 进度条
- `questionary` - 交互式提示（用于配置初始化）

**服务器**：
- `FastAPI` - 现代异步 Web 框架
- `uvicorn[standard]` - 支持 websocket 的 ASGI 服务器
- `marker` - PDF 到 Markdown 转换引擎
- `python-multipart` - Multipart 表单数据解析
- `aiofiles` - 异步文件操作
- `structlog` - 结构化日志

**开发**：
- `pyproject.toml` - 现代 Python 打包
- `ruff` - 快速 linter 和格式化程序
- `pytest` - 测试框架
- `pytest-asyncio` - 异步测试支持
- `pytest-cov` - 覆盖率报告
- `mypy` - 可选的静态类型检查

**理由**：
- ✅ **SOLID**：每个库都有单一、明确的用途
- ✅ **DRY**：无重叠功能（例如，httpx 替换 requests）
- ✅ **YAGNI**：无不必要的抽象（例如，还没有 Celery）
- ✅ **现代**：所有库都积极维护，Python 3.11+ 兼容

### 10.2 依赖图

```
client/
├── typer (CLI 框架)
│   └── pydantic (验证)
├── httpx (HTTP 客户端)
│   └── anyio (异步后端)
├── tqdm (进度条)
└── questionary (提示)

server/
├── FastAPI (Web 框架)
│   ├── pydantic (验证)
│   ├── starlette (ASGI 工具包)
│   └── anyio (异步后端)
├── uvicorn (ASGI 服务器)
│   └── uvloop (事件循环，仅 Unix)
├── marker (PDF 转换)
│   ├── torch (GPU 支持)
│   └── transformers (OCR 模型)
├── python-multipart (表单解析)
├── aiofiles (异步文件 I/O)
│   └── aioconsole (异步 stdio)
└── structlog (日志)
    └── python-json-logger (JSON 输出)
```

### 10.3 Python 版本

**目标**：Python 3.11+
**理由**：
- 现代异步/等待语法
- 更好的类型提示（`|` 联合运算符）
- 性能改进
- 更简洁代码的 `Self` 类型
- 异常组（`ExceptionGroup`）

**最低**：3.10（如果需要兼容性）
**不支持**：< 3.10（缺少关键功能）

---

## 11. 部署架构

### 11.1 开发环境

**本地开发**：
```bash
# 客户端（任何机器）
$ cd client
$ python -m venv .venv
$ source .venv/bin/activate  # Windows: .venv\Scripts\activate
$ pip install -e .

# 服务器（GPU 机器）
$ cd server
$ python -m venv .venv
$ source .venv/bin/activate
$ pip install -e .
$ uvicorn server.main:app --reload --port 8000
```

**配置**：
```bash
# 初始化客户端配置
$ pdf2md config init --server-url http://localhost:8000

# 测试连接
$ pdf2md test-connection
✓ 已连接到服务器 (version 1.0.0)
```

### 11.2 生产部署

**Docker 部署（推荐）**：

**Dockerfile**（服务器）：
```dockerfile
FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

# 安装 Python
RUN apt-get update && apt-get install -y python3.11 python3-pip

# 安装系统依赖
RUN apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1

# 设置工作目录
WORKDIR /app

# 安装 Python 依赖
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# 复制应用
COPY server/ server/

# 创建临时目录
RUN mkdir -p /tmp/pdf2md

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# 运行服务器
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Docker Compose**：
```yaml
version: '3.8'

services:
  pdf2md-server:
    build: .
    container_name: pdf2md-server
    ports:
      - "8000:8000"
    volumes:
      - /tmp/pdf2md:/tmp/pdf2md
    environment:
      - CUDA_VISIBLE_DEVICES=0
      - TMPDIR=/tmp/pdf2md
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

**部署命令**：
```bash
# 构建镜像
$ docker build -t pdf2md-server:1.0 .

# 运行容器
$ docker-compose up -d

# 查看日志
$ docker-compose logs -f

# 停止
$ docker-compose down
```

### 11.3 Systemd 服务（替代方案）

**服务文件**：`/etc/systemd/system/pdf2md.service`
```ini
[Unit]
Description=PDF2MD 转换服务
After=network.target

[Service]
Type=simple
User=pdf2md
WorkingDirectory=/opt/pdf2md
Environment="PATH=/opt/pdf2md/venv/bin"
ExecStart=/opt/pdf2md/venv/bin/uvicorn server.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**命令**：
```bash
# 启用服务
$ sudo systemctl enable pdf2md

# 启动服务
$ sudo systemctl start pdf2md

# 检查状态
$ sudo systemctl status pdf2md

# 查看日志
$ sudo journalctl -u pdf2md -f
```

### 11.4 监控和日志

**结构化日志**：
```python
import structlog

logger = structlog.get_logger()

# 记录转换开始
logger.info(
    "conversion_started",
    job_id=job_id,
    filename=sanitized_filename,
    file_size=file_size,
    client_ip=request.client.host
)

# 记录转换完成
logger.info(
    "conversion_completed",
    job_id=job_id,
    pages_processed=pages,
    duration_seconds=duration,
    output_size_bytes=output_size
)

# 记录错误
logger.error(
    "conversion_failed",
    job_id=job_id,
    error=str(e),
    error_type=type(e).__name__,
    traceback=traceback.format_exc()
)
```

**健康检查端点**：
```python
@app.get("/health")
async def health_check():
    """负载均衡器的健康检查。"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "gpu_available": torch.cuda.is_available(),
        "active_conversions": conversion_semaphore._value,
        "uptime_seconds": time.time() - start_time
    }
```

---

## 12. 性能考虑

### 12.1 性能目标

**来自成功标准**：
- **SC-001**：在 30 秒内转换 10 页 PDF
- **SC-004**：支持 10 个并发请求
- **FR-012**：处理最大 500MB 的文件

### 12.2 瓶颈分析

**预期时间分解**（10 页 PDF）：
```
总计：30 秒

1. 文件上传（5 秒）：
   - 网络传输：3 秒
   - 磁盘写入：2 秒

2. 文件验证（1 秒）：
   - 类型检查：0.1 秒
   - 大小检查：0.1 秒
   - 病毒扫描（可选）：0.8 秒

3. PDF 转换（20 秒）：
   - 加载 PDF：1 秒
   - 提取文本：5 秒
   - OCR（GPU）：12 秒
   - 生成 MD：2 秒

4. 文件下载（4 秒）：
   - 磁盘读取：1 秒
   - 网络传输：3 秒
```

### 12.3 优化策略

**网络优化**：
- 使用压缩（GZip 中间件）
- 增加大文件的块大小
- 如果支持，启用 HTTP/2

**转换优化**：
- 对多页 PDF 使用批处理
- 缓存常用的 OCR 模型
- 启动时预热 GPU

**并发优化**：
- 使用 asyncio 进行并发 I/O
- 信号量限制 GPU 使用
- 队列系统用于未来扩展

**文件 I/O 优化**：
- 使用异步文件操作（aiofiles）
- 流式上传/下载（不缓冲整个文件）
- 使用更快的存储（SSD vs HDD）

### 12.4 缓存策略（未来）

**不在 MVP 中**（YAGNI），但潜在的未来改进：
- 缓存转换的 Markdown（基于哈希）
- 启动时预加载 OCR 模型
- CDN 用于静态资产（如果添加 Web UI）

---

## 13. 测试策略

### 13.1 测试金字塔

```
        /\
       /  \
      / 端到端 \         (10% - 集成测试)
     /--------\
    /  契约测试 \     (20% - API 契约测试)
   /--------------\
  /    单元测试    \ (70% - 组件测试)
 /--------------------\
```

### 13.2 单元测试

**客户端测试**（`tests/unit/test_client/`）：
```python
def test_validate_pdf_file_success(tmp_path):
    """测试有效的 PDF 验证。"""
    pdf_file = create_test_pdf(tmp_path, "test.pdf")
    validate_pdf_file(pdf_file)  # 不应引发

def test_validate_pdf_file_not_found(tmp_path):
    """测试缺失文件引发错误。"""
    with pytest.raises(FileValidationError):
        validate_pdf_file(tmp_path / "missing.pdf")

def test_config_load_default():
    """测试加载默认配置。"""
    config = load_config()
    assert config.server_url == "http://localhost:8000"
    assert config.timeout == 300

def test_config_hierarchy():
    """测试配置优先级：CLI > env > file > default。"""
    # 测试环境变量覆盖
    os.environ["PDF2MD_SERVER_URL"] = "http://example.com"
    config = load_config()
    assert config.server_url == "http://example.com"
```

**服务器测试**（`tests/unit/test_server/`）：
```python
def test_file_manager_save_upload(tmp_path):
    """测试保存上传文件。"""
    manager = TempFileManager(tmp_path)

    # 创建模拟上传
    upload = MockUploadFile("test.pdf", b"%PDF-1.4...")

    # 保存上传
    path = asyncio.run(manager.save_upload(upload))

    # 验证文件存在
    assert path.exists()
    assert path.name.startswith(upload.filename)

async def test_converter_success(tmp_path):
    """测试成功转换。"""
    converter = MarkerConverter()
    pdf_path = create_test_pdf(tmp_path, "input.pdf")
    md_path = tmp_path / "output.md"

    await converter.convert(pdf_path, md_path)

    assert md_path.exists()
    assert "# Test PDF" in md_path.read_text()
```

### 13.3 契约测试

**API 契约测试**（`tests/contract/`）：
```python
def test_convert_endpoint_contract(client):
    """测试 /convert 端点契约。"""
    # 创建测试 PDF
    pdf_content = b"%PDF-1.4\ntest content"

    # 发送请求
    response = client.post(
        "/convert",
        files={"file": ("test.pdf", pdf_content, "application/pdf")}
    )

    # 断言响应格式
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/markdown"
    assert "content-disposition" in response.headers

def test_convert_invalid_file_type(client):
    """测试非 PDF 文件的 400 错误。"""
    response = client.post(
        "/convert",
        files={"file": ("test.txt", b"not a pdf", "text/plain")}
    )

    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "detail" in data
```

### 13.4 集成测试

**端到端测试**（`tests/integration/`）：
```python
@pytest.mark.asyncio
async def test_conversion_flow(server, client, tmp_path):
    """测试完整转换流程。"""
    # 启动服务器
    async with server:
        # 创建测试 PDF
        pdf_path = create_test_pdf(tmp_path, "document.pdf")

        # 使用客户端转换
        result = await client.convert(pdf_path)

        # 验证输出
        assert result.exists()
        assert result.suffix == ".md"
        assert "# Test PDF" in result.read_text()

@pytest.mark.asyncio
async def test_network_error_recovery(server, client, tmp_path):
    """测试网络错误时的重试。"""
    # 延迟后启动服务器
    async with delayed_server(delay=2):
        pdf_path = create_test_pdf(tmp_path, "test.pdf")

        # 应该重试并成功
        result = await client.convert(pdf_path)
        assert result.exists()
```

### 13.5 性能测试

**基准测试**（`tests/performance/`）：
```python
def test_conversion_performance_10_pages(benchmark, tmp_path):
    """基准测试 10 页 PDF 转换。"""
    pdf_path = create_test_pdf(tmp_path, "10pages.pdf", pages=10)

    result = benchmark.pedantic(
        convert_pdf,
        args=(pdf_path,)
    )

    # 断言 < 30 秒
    assert benchmark.stats.stats.mean < 30

def test_concurrent_requests_10_concurrent(tmp_path):
    """测试 10 个并发转换。"""
    async def convert_10():
        tasks = [convert_pdf(create_test_pdf(tmp_path, f"{i}.pdf"))
                 for i in range(10)]
        await asyncio.gather(*tasks)

    # 应该无错误完成
    asyncio.run(convert_10())
```

### 13.6 测试覆盖率目标

**最低覆盖率**：
- 关键路径：90%+
- 平均覆盖率：80%+
- 总体：75%+

**从覆盖率中排除**：
- 测试文件
- 配置存根
- `__init__.py`
- 类型定义

---

## 附录 A：配置文件示例

**`~/.pdf2md/config.json`**：
```json
{
  "server_url": "http://192.168.1.100:8000",
  "timeout": 300,
  "chunk_size": 8192,
  "max_retries": 3,
  "verify_ssl": true,
  "output_dir": null,
  "overwrite": false
}
```

## 附录 B：环境变量

| 变量 | 描述 | 默认值 |
|------|------|--------|
| `PDF2MD_SERVER_URL` | 服务器 URL | `http://localhost:8000` |
| `PDF2MD_TIMEOUT` | 请求超时（秒） | `300` |
| `PDF2MD_CONFIG_PATH` | 配置文件路径 | `~/.pdf2md/config.json` |
| `PDF2MD_VERBOSE` | 启用详细日志 | `false` |

## 附录 C：退出代码

| 代码 | 含义 |
|------|------|
| 0 | 成功 |
| 1 | 通用错误 |
| 2 | 网络错误 |
| 3 | 验证错误 |
| 4 | 转换错误 |
| 5 | 配置错误 |

## 附录 D：错误代码参考

| 代码 | 描述 | 可重试 |
|------|------|--------|
| `ConnectionError` | 无法连接到服务器 | 是 |
| `TimeoutError` | 请求超时 | 是 |
| `ValidationError` | 无效文件输入 | 否 |
| `ConversionError` | PDF 转换失败 | 否 |
| `ResourceError` | 服务器内存不足 | 是（延迟后） |
| `ConfigError` | 无效配置 | 否 |

---

**文档版本**：1.0
**最后更新**：2026-01-06
**下次审查**：MVP 实现后
