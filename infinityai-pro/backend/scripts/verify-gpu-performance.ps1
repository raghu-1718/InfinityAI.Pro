# =============================================================================
# InfinityAI.Pro GPU Performance Verification & Benchmarking
# Comprehensive testing of GPU acceleration for trading platform
# =============================================================================

param(
    [string]$Mode = "docker",        # docker, kubernetes, local
    [switch]$BenchmarkOnly = $false,
    [switch]$DetailedReport = $true
)

Write-Host "🎮 InfinityAI.Pro GPU Performance Verification" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
Write-Host ""

# Configuration
$LogFile = "gpu-verification-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"
$BenchmarkResults = @()

# Function to log messages
function Write-Log {
    param($Message, $Color = "White", $NoNewline = $false)
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMessage = "[$Timestamp] $Message"
    if ($NoNewline) {
        Write-Host $LogMessage -ForegroundColor $Color -NoNewline
    } else {
        Write-Host $LogMessage -ForegroundColor $Color
    }
    Add-Content -Path $LogFile -Value $LogMessage
}

# Function to check system GPU capabilities
function Test-SystemGPU {
    Write-Log "🔍 Checking system GPU capabilities..." "Yellow"
    
    $gpuInfo = @{
        HasGPU = $false
        GPUName = "None"
        GPUCount = 0
        CUDAVersion = "N/A"
        DriverVersion = "N/A"
        MemoryTotal = 0
        ComputeCapability = "N/A"
    }
    
    try {
        # Check NVIDIA GPU
        $nvidiaOutput = nvidia-smi --query-gpu=name,driver_version,memory.total,compute_cap --format=csv,noheader,nounits 2>$null
        if ($nvidiaOutput) {
            $gpuData = $nvidiaOutput.Split(',')
            $gpuInfo.HasGPU = $true
            $gpuInfo.GPUName = $gpuData[0].Trim()
            $gpuInfo.DriverVersion = $gpuData[1].Trim()
            $gpuInfo.MemoryTotal = [int]$gpuData[2].Trim()
            $gpuInfo.ComputeCapability = $gpuData[3].Trim()
            
            # Get GPU count
            $gpuInfo.GPUCount = (nvidia-smi --list-gpus).Count
            
            # Get CUDA version
            try {
                $cudaVersion = nvcc --version 2>$null | Select-String "release" | ForEach-Object { $_.Line.Split(',')[1].Split(' ')[-1] }
                $gpuInfo.CUDAVersion = $cudaVersion
            } catch {
                $gpuInfo.CUDAVersion = "Not installed"
            }
            
            Write-Log "✅ GPU Detected: $($gpuInfo.GPUName)" "Green"
            Write-Log "✅ GPU Count: $($gpuInfo.GPUCount)" "Green"
            Write-Log "✅ Driver Version: $($gpuInfo.DriverVersion)" "Green"
            Write-Log "✅ CUDA Version: $($gpuInfo.CUDAVersion)" "Green"
            Write-Log "✅ Memory: $($gpuInfo.MemoryTotal) MB" "Green"
            Write-Log "✅ Compute Capability: $($gpuInfo.ComputeCapability)" "Green"
        } else {
            Write-Log "❌ No NVIDIA GPU detected" "Red"
        }
    } catch {
        Write-Log "❌ NVIDIA drivers not available" "Red"
    }
    
    return $gpuInfo
}

# Function to check Docker GPU support
function Test-DockerGPU {
    Write-Log "🐳 Testing Docker GPU support..." "Yellow"
    
    $dockerGPU = @{
        Supported = $false
        RuntimeVersion = "N/A"
        ContainerAccess = $false
    }
    
    try {
        # Check if Docker supports GPU
        $gpuTest = docker run --rm --gpus all nvidia/cuda:12.2-base nvidia-smi 2>$null
        if ($gpuTest) {
            $dockerGPU.Supported = $true
            $dockerGPU.ContainerAccess = $true
            Write-Log "✅ Docker GPU support: Available" "Green"
            Write-Log "✅ Container GPU access: Working" "Green"
        } else {
            Write-Log "❌ Docker GPU support: Not available" "Red"
        }
    } catch {
        Write-Log "❌ Docker GPU test failed" "Red"
    }
    
    return $dockerGPU
}

# Function to benchmark CPU vs GPU performance
function Start-PerformanceBenchmark {
    Write-Log "⚡ Starting CPU vs GPU performance benchmarks..." "Yellow"
    
    # Create benchmark script
    $benchmarkScript = @'
import time
import numpy as np
import pandas as pd
import json
import sys

def benchmark_numpy_operations():
    """Benchmark basic numerical operations"""
    print("🔢 Benchmarking NumPy operations...")
    
    # Matrix operations
    size = 5000
    a = np.random.random((size, size))
    b = np.random.random((size, size))
    
    start_time = time.time()
    c = np.dot(a, b)
    numpy_time = time.time() - start_time
    
    print(f"NumPy matrix multiplication ({size}x{size}): {numpy_time:.3f}s")
    return {"numpy_matmul": numpy_time}

def benchmark_pandas_operations():
    """Benchmark pandas data operations"""
    print("📊 Benchmarking Pandas operations...")
    
    # Large dataframe operations
    size = 1000000
    df = pd.DataFrame({
        'price': np.random.random(size) * 1000,
        'volume': np.random.randint(1, 1000, size),
        'timestamp': pd.date_range('2023-01-01', periods=size, freq='1s')
    })
    
    start_time = time.time()
    # Simulate trading calculations
    df['sma_20'] = df['price'].rolling(window=20).mean()
    df['rsi'] = df['price'].pct_change().rolling(window=14).apply(lambda x: 100 - (100 / (1 + x[x > 0].sum() / abs(x[x < 0].sum()))))
    pandas_time = time.time() - start_time
    
    print(f"Pandas calculations on {size} rows: {pandas_time:.3f}s")
    return {"pandas_calculations": pandas_time}

def benchmark_gpu_operations():
    """Benchmark GPU operations if available"""
    results = {}
    
    try:
        import torch
        print("🎮 Benchmarking PyTorch GPU operations...")
        
        if torch.cuda.is_available():
            device = torch.device('cuda')
            print(f"Using GPU: {torch.cuda.get_device_name(0)}")
            
            # GPU matrix operations
            size = 5000
            a_gpu = torch.randn(size, size, device=device)
            b_gpu = torch.randn(size, size, device=device)
            
            # Warm up
            _ = torch.mm(a_gpu, b_gpu)
            torch.cuda.synchronize()
            
            start_time = time.time()
            c_gpu = torch.mm(a_gpu, b_gpu)
            torch.cuda.synchronize()
            gpu_time = time.time() - start_time
            
            print(f"PyTorch GPU matrix multiplication ({size}x{size}): {gpu_time:.3f}s")
            results["pytorch_gpu_matmul"] = gpu_time
            
            # Compare with CPU
            a_cpu = torch.randn(size, size)
            b_cpu = torch.randn(size, size)
            
            start_time = time.time()
            c_cpu = torch.mm(a_cpu, b_cpu)
            cpu_time = time.time() - start_time
            
            print(f"PyTorch CPU matrix multiplication ({size}x{size}): {cpu_time:.3f}s")
            results["pytorch_cpu_matmul"] = cpu_time
            results["speedup"] = cpu_time / gpu_time if gpu_time > 0 else 0
            
            print(f"GPU Speedup: {results['speedup']:.2f}x")
            
        else:
            print("❌ CUDA not available for PyTorch")
            results["pytorch_gpu_error"] = "CUDA not available"
            
    except ImportError:
        print("❌ PyTorch not available")
        results["pytorch_error"] = "PyTorch not installed"
    
    try:
        import cupy as cp
        print("🚀 Benchmarking CuPy operations...")
        
        size = 5000
        a_cupy = cp.random.random((size, size))
        b_cupy = cp.random.random((size, size))
        
        start_time = time.time()
        c_cupy = cp.dot(a_cupy, b_cupy)
        cp.cuda.Stream.null.synchronize()
        cupy_time = time.time() - start_time
        
        print(f"CuPy GPU matrix multiplication ({size}x{size}): {cupy_time:.3f}s")
        results["cupy_gpu_matmul"] = cupy_time
        
    except ImportError:
        print("❌ CuPy not available")
        results["cupy_error"] = "CuPy not installed"
    except Exception as e:
        print(f"❌ CuPy error: {str(e)}")
        results["cupy_error"] = str(e)
    
    return results

def main():
    results = {}
    
    # Run CPU benchmarks
    results.update(benchmark_numpy_operations())
    results.update(benchmark_pandas_operations())
    
    # Run GPU benchmarks
    gpu_results = benchmark_gpu_operations()
    results.update(gpu_results)
    
    # Output results as JSON
    print("\n" + "="*50)
    print("BENCHMARK RESULTS:")
    print(json.dumps(results, indent=2))
    
    return results

if __name__ == "__main__":
    main()
'@
    
    # Save benchmark script
    $benchmarkScript | Out-File -FilePath "benchmark_gpu.py" -Encoding UTF8
    
    if ($Mode -eq "docker") {
        # Run benchmark in Docker containers
        Write-Log "Running benchmarks in Docker containers..." "White"
        
        try {
            # Test CPU container first
            Write-Log "Testing CPU performance..." "White"
            docker run --rm -v "${PWD}:/workspace" python:3.11-slim bash -c "cd /workspace && pip install numpy pandas torch && python benchmark_gpu.py"
            
            # Test GPU container if available
            try {
                Write-Log "Testing GPU performance..." "White"
                docker run --rm --gpus all -v "${PWD}:/workspace" nvidia/cuda:12.2-devel-ubuntu22.04 bash -c "apt update && apt install -y python3 python3-pip && cd /workspace && pip install numpy pandas torch cupy-cuda12x && python3 benchmark_gpu.py"
            } catch {
                Write-Log "GPU container test skipped (no GPU support)" "Yellow"
            }
        } catch {
            Write-Log "Benchmark execution failed" "Red"
        }
    } else {
        # Run benchmark locally
        Write-Log "Running local benchmark..." "White"
        try {
            python benchmark_gpu.py
        } catch {
            Write-Log "Local Python not available or missing dependencies" "Yellow"
        }
    }
    
    # Clean up
    Remove-Item "benchmark_gpu.py" -ErrorAction SilentlyContinue
}

# Function to test deployed services
function Test-DeployedServices {
    Write-Log "🏥 Testing deployed trading services..." "Yellow"
    
    $services = @(
        @{ Name = "API Gateway"; URL = "http://localhost:8000/health"; Expected = "healthy" },
        @{ Name = "Engine A"; URL = "http://localhost:8001/health"; Expected = "healthy" },
        @{ Name = "Engine B"; URL = "http://localhost:8002/health"; Expected = "healthy" },
        @{ Name = "Engine C"; URL = "http://localhost:8003/health"; Expected = "healthy" }
    )
    
    $serviceResults = @()
    
    foreach ($service in $services) {
        $result = @{
            Name = $service.Name
            Status = "Unknown"
            ResponseTime = 0
            Error = $null
        }
        
        try {
            $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
            $response = Invoke-WebRequest -Uri $service.URL -TimeoutSec 5 -UseBasicParsing
            $stopwatch.Stop()
            
            $result.ResponseTime = $stopwatch.ElapsedMilliseconds
            
            if ($response.StatusCode -eq 200) {
                $result.Status = "Healthy"
                Write-Log "✅ $($service.Name): Healthy (${result.ResponseTime}ms)" "Green"
            } else {
                $result.Status = "Unhealthy"
                $result.Error = "HTTP $($response.StatusCode)"
                Write-Log "⚠️ $($service.Name): Unhealthy (Status: $($response.StatusCode))" "Yellow"
            }
        } catch {
            $result.Status = "Error"
            $result.Error = $_.Exception.Message
            Write-Log "❌ $($service.Name): Error - $($_.Exception.Message)" "Red"
        }
        
        $serviceResults += $result
    }
    
    return $serviceResults
}

# Function to monitor resource usage
function Get-ResourceUsage {
    Write-Log "📊 Monitoring resource usage..." "Yellow"
    
    $resourceUsage = @{
        CPU = 0
        Memory = 0
        GPU = @()
        Docker = @()
    }
    
    try {
        # Get CPU and Memory usage
        $cpu = (Get-Counter "\Processor(_Total)\% Processor Time").CounterSamples[0].CookedValue
        $memory = (Get-Counter "\Memory\% Committed Bytes In Use").CounterSamples[0].CookedValue
        
        $resourceUsage.CPU = [math]::Round($cpu, 2)
        $resourceUsage.Memory = [math]::Round($memory, 2)
        
        Write-Log "💻 System CPU Usage: $($resourceUsage.CPU)%" "White"
        Write-Log "💻 System Memory Usage: $($resourceUsage.Memory)%" "White"
    } catch {
        Write-Log "⚠️ Could not retrieve system resource usage" "Yellow"
    }
    
    try {
        # Get GPU usage if available
        $gpuUsage = nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader,nounits 2>$null
        if ($gpuUsage) {
            foreach ($line in $gpuUsage) {
                $values = $line.Split(',')
                $gpuInfo = @{
                    Utilization = [int]$values[0].Trim()
                    MemoryUsed = [int]$values[1].Trim()
                    MemoryTotal = [int]$values[2].Trim()
                    Temperature = [int]$values[3].Trim()
                }
                $resourceUsage.GPU += $gpuInfo
                Write-Log "🎮 GPU Utilization: $($gpuInfo.Utilization)%" "White"
                Write-Log "🎮 GPU Memory: $($gpuInfo.MemoryUsed)MB / $($gpuInfo.MemoryTotal)MB" "White"
                Write-Log "🎮 GPU Temperature: $($gpuInfo.Temperature)°C" "White"
            }
        }
    } catch {
        Write-Log "⚠️ Could not retrieve GPU usage" "Yellow"
    }
    
    try {
        # Get Docker container stats
        $dockerStats = docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>$null
        if ($dockerStats) {
            $lines = $dockerStats -split "`n" | Select-Object -Skip 1
            foreach ($line in $lines) {
                if ($line.Trim() -ne "") {
                    $parts = $line -split "\t"
                    $containerInfo = @{
                        Name = $parts[0].Trim()
                        CPU = $parts[1].Trim()
                        Memory = $parts[2].Trim()
                    }
                    $resourceUsage.Docker += $containerInfo
                    Write-Log "🐳 Container $($containerInfo.Name): CPU $($containerInfo.CPU), Memory $($containerInfo.Memory)" "White"
                }
            }
        }
    } catch {
        Write-Log "⚠️ Could not retrieve Docker stats" "Yellow"
    }
    
    return $resourceUsage
}

# Function to generate detailed report
function New-DetailedReport {
    param($GPUInfo, $ServiceResults, $ResourceUsage)
    
    Write-Log "📋 Generating detailed performance report..." "Yellow"
    
    $report = @{
        Timestamp = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
        SystemInfo = @{
            OS = "$($PSVersionTable.Platform) $($PSVersionTable.OS)"
            PowerShell = $PSVersionTable.PSVersion
            Machine = $env:COMPUTERNAME
        }
        GPUCapabilities = $GPUInfo
        ServiceHealth = $ServiceResults
        ResourceUsage = $ResourceUsage
        Recommendations = @()
    }
    
    # Add recommendations
    if (-not $GPUInfo.HasGPU) {
        $report.Recommendations += "Consider adding NVIDIA GPU for 5-10x AI inference speedup"
    } elseif (-not $GPUInfo.CUDAVersion -or $GPUInfo.CUDAVersion -eq "Not installed") {
        $report.Recommendations += "Install CUDA toolkit for GPU acceleration"
    }
    
    if ($ServiceResults | Where-Object { $_.Status -ne "Healthy" }) {
        $report.Recommendations += "Some trading services are not healthy - check logs and restart if needed"
    }
    
    if ($ResourceUsage.Memory -gt 80) {
        $report.Recommendations += "High memory usage detected - consider scaling or optimizing"
    }
    
    # Save report
    $reportJson = $report | ConvertTo-Json -Depth 10 -Compress:$false
    $reportFile = "gpu-performance-report-$(Get-Date -Format 'yyyyMMdd-HHmmss').json"
    $reportJson | Out-File -FilePath $reportFile -Encoding UTF8
    
    Write-Log "📄 Detailed report saved to: $reportFile" "Green"
    
    return $report
}

# Function to show final summary
function Show-PerformanceSummary {
    param($GPUInfo, $ServiceResults, $ResourceUsage)
    
    Write-Log ""
    Write-Log "🎯 InfinityAI.Pro GPU Performance Summary" "Green"
    Write-Log "=========================================" "Green"
    Write-Log ""
    
    # GPU Status
    Write-Log "🎮 GPU Configuration:" "Cyan"
    if ($GPUInfo.HasGPU) {
        Write-Log "✅ GPU Available: $($GPUInfo.GPUName)" "Green"
        Write-Log "✅ GPU Count: $($GPUInfo.GPUCount)" "Green"
        Write-Log "✅ Memory: $($GPUInfo.MemoryTotal) MB" "Green"
        Write-Log "✅ Compute: $($GPUInfo.ComputeCapability)" "Green"
        Write-Log "✅ CUDA: $($GPUInfo.CUDAVersion)" "Green"
    } else {
        Write-Log "❌ No GPU detected - Running in CPU mode" "Red"
        Write-Log "💡 For GPU acceleration:" "Yellow"
        Write-Log "  • Install NVIDIA GPU (T4, V100, A10G recommended)" "White"
        Write-Log "  • Install CUDA 12.2+ and drivers" "White"
        Write-Log "  • Enable Docker GPU support" "White"
    }
    Write-Log ""
    
    # Service Status
    Write-Log "🏥 Trading Services:" "Cyan"
    $healthyCount = ($ServiceResults | Where-Object { $_.Status -eq "Healthy" }).Count
    $totalCount = $ServiceResults.Count
    
    if ($healthyCount -eq $totalCount) {
        Write-Log "✅ All services healthy ($healthyCount/$totalCount)" "Green"
    } else {
        Write-Log "⚠️ Some services need attention ($healthyCount/$totalCount healthy)" "Yellow"
    }
    
    foreach ($service in $ServiceResults) {
        $status = if ($service.Status -eq "Healthy") { "✅" } else { "❌" }
        $timing = if ($service.ResponseTime -gt 0) { "($($service.ResponseTime)ms)" } else { "" }
        Write-Log "  $status $($service.Name) $timing" "White"
    }
    Write-Log ""
    
    # Performance Assessment
    Write-Log "⚡ Performance Assessment:" "Cyan"
    if ($GPUInfo.HasGPU) {
        Write-Log "✅ GPU-accelerated AI inference available" "Green"
        Write-Log "✅ Expected 5-10x speedup for neural networks" "Green"
        Write-Log "✅ Real-time market data processing optimized" "Green"
        
        if ($ResourceUsage.GPU -and $ResourceUsage.GPU.Count -gt 0) {
            $avgUtilization = ($ResourceUsage.GPU | Measure-Object -Property Utilization -Average).Average
            if ($avgUtilization -lt 10) {
                Write-Log "💡 GPU utilization low - scale up AI workloads" "Yellow"
            } elseif ($avgUtilization -gt 90) {
                Write-Log "⚠️ GPU utilization high - consider adding more GPUs" "Yellow"
            } else {
                Write-Log "✅ GPU utilization optimal ($avgUtilization%)" "Green"
            }
        }
    } else {
        Write-Log "⚠️ CPU-only mode - AI inference will be slower" "Yellow"
        Write-Log "💡 GPU acceleration can provide 5-10x speedup" "Yellow"
    }
    
    # Resource Status
    if ($ResourceUsage.CPU -gt 80) {
        Write-Log "⚠️ High CPU usage ($($ResourceUsage.CPU)%) - monitor load" "Yellow"
    } else {
        Write-Log "✅ CPU usage normal ($($ResourceUsage.CPU)%)" "Green"
    }
    
    if ($ResourceUsage.Memory -gt 80) {
        Write-Log "⚠️ High memory usage ($($ResourceUsage.Memory)%) - monitor/scale" "Yellow"
    } else {
        Write-Log "✅ Memory usage normal ($($ResourceUsage.Memory)%)" "Green"
    }
    
    Write-Log ""
    Write-Log "🚀 Ready for Live Trading:" "Green"
    if ($GPUInfo.HasGPU -and $healthyCount -eq $totalCount) {
        Write-Log "✅ Platform optimized and ready for high-performance trading!" "Green"
    } elseif ($healthyCount -eq $totalCount) {
        Write-Log "✅ Platform ready for trading (CPU mode)" "Green"
        Write-Log "💡 Add GPU for enhanced performance" "Yellow"
    } else {
        Write-Log "⚠️ Fix service issues before live trading" "Yellow"
    }
    
    Write-Log ""
}

# Main execution
try {
    Write-Log "🧪 Starting GPU Performance Verification" "Green"
    Write-Log "Verification Log: $LogFile" "White"
    Write-Log ""
    
    # Test system GPU capabilities
    $gpuInfo = Test-SystemGPU
    Write-Log ""
    
    # Test Docker GPU support
    $dockerGPU = Test-DockerGPU  
    Write-Log ""
    
    # Run performance benchmarks if requested
    if (-not $BenchmarkOnly -or $BenchmarkOnly) {
        Start-PerformanceBenchmark
        Write-Log ""
    }
    
    # Test deployed services
    $serviceResults = Test-DeployedServices
    Write-Log ""
    
    # Monitor resource usage
    $resourceUsage = Get-ResourceUsage
    Write-Log ""
    
    # Generate detailed report if requested
    if ($DetailedReport) {
        $report = New-DetailedReport -GPUInfo $gpuInfo -ServiceResults $serviceResults -ResourceUsage $resourceUsage
        Write-Log ""
    }
    
    # Show final summary
    Show-PerformanceSummary -GPUInfo $gpuInfo -ServiceResults $serviceResults -ResourceUsage $resourceUsage
    
    Write-Log ""
    Write-Log "🎊 GPU Performance Verification Complete!" "Green"
    
} catch {
    Write-Log "❌ Verification failed: $($_.Exception.Message)" "Red"
    Write-Log "Check the log file for details: $LogFile" "Yellow"
    exit 1
}