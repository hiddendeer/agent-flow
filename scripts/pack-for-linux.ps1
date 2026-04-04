# DeerFlow Migration Packager for Linux
# 这个脚本会自动排除大体积的依赖和临时目录，只打包核心源码供迁移。

$projectName = "agent-flow-migration.zip"
$rootPath = Get-Location

# 定义需要排除的目录（相对路径）
$excludeDirs = @(
    "frontend/node_modules",
    "frontend/.next",
    "backend/.venv",
    "backend/.deer-flow",
    "backend/.langgraph_api",
    "**/__pycache__",
    ".git",
    "dist",
    "temp",
    "logs"
)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  DeerFlow 源码打包工具 (Windows -> Linux)" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# 提示：如果文件已存在，先删除旧的
if (Test-Path $projectName) {
    Remove-Item $projectName
    Write-Host "已清理旧的压缩包: $projectName" -ForegroundColor Yellow
}

Write-Host "正在扫描并打包源码 (排除冗余目录)..." -ForegroundColor Gray

# 构建 7-Zip 或系统自带 tar 的排除列表并压缩
# Windows 10/11 默认自带 tar 命令
$tarCmd = "tar"
$excludeArgs = @()
foreach ($dir in $excludeDirs) {
    $excludeArgs += "--exclude='$dir'"
}

# 执行压缩命令
# 注意：cd .. && tar 的目的是让压缩包内部不带有冗余的父目录结构
Invoke-Expression "$tarCmd -czvf $projectName $excludeArgs ."

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host "  打包成功！" -ForegroundColor Green
    Write-Host "  文件: $projectName" -ForegroundColor Green
    Write-Host "  大小: " -NoNewline -ForegroundColor Green
    Write-Host "$((Get-Item $projectName).Length / 1MB | ForEach-Object { '{0:N2}' -f $_ }) MB" -ForegroundColor White
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "操作提示:"
    Write-Host "1. 将 $projectName 拷贝到 Linux 服务器。"
    Write-Host "2. 在 Linux 上运行: unzip $projectName 或 tar -xzvf $projectName"
    Write-Host "3. 执行 scripts/deploy-backend-only.sh 进行部署。"
} else {
    Write-Host "打包失败，请检查报错信息。" -ForegroundColor Red
}
