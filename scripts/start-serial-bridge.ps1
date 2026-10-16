# Starts the ESP32 Base Station Serial Bridge on COM13
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$rootDir = Split-Path -Parent $scriptDir
Set-Location $rootDir

Write-Host "Starting ESP32 Serial Bridge for Base Station on COM13..." -ForegroundColor Cyan
& "$rootDir\.venv\Scripts\python.exe" "$rootDir\hardware\bridge\serial_bridge.py" COM13
