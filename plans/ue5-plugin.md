# UE5 Plugin Architecture

## Overview

The mg-rs UE5 plugin provides integration between the mg-rs graphics and compute runtime and Unreal Engine 5.

## Plugin Structure

```
MGRS_UE5_Plugin/
├── Source/
│   ├── MGRSRuntime/
│   │   ├── MGRSRuntime.Build.cs
│   │   ├── Private/
│   │   │   ├── MGRSContext.cpp
│   │   │   ├── MGRSResource.cpp
│   │   │   ├── MGRSPipeline.cpp
│   │   │   ├── MGRSCommandBuffer.cpp
│   │   │   └── MGRSBlueprintFunctionLibrary.cpp
│   │   └── Public/
│   │       ├── MGRSContext.h
│   │       ├── MGRSResource.h
│   │       ├── MGRSPipeline.h
│   │       ├── MGRSCommandBuffer.h
│   │       └── MGRSBlueprintFunctionLibrary.h
│   └── ThirdParty/
│       └── mg-rs/
│           ├── include/
│           └── lib/
├── Content/
│   ├── Blueprints/
│   ├── Materials/
│   └── Textures/
├── Resources/
├── .uplugin
└── README.md
```

## Core Classes

### AMGRSContext

```cpp
class AMGRSContext : public AActor {
    GENERATED_BODY()

public:
    // Initialization
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

    // Device management
    int32 GetDeviceCount() const;
    FString GetDeviceName(int32 DeviceIndex) const;
    int32 GetSelectedDeviceIndex() const;
    void SetSelectedDeviceIndex(int32 DeviceIndex);

    // Resource creation
    UMGRSBuffer* CreateBuffer(int32 Size, EBufferUsage Usage);
    UMGRSImage* CreateImage(int32 Width, int32 Height, EImageFormat Format, EImageUsage Usage);

    // Command buffer management
    UMGRSCommandBuffer* CreateCommandBuffer();
    void SubmitCommandBuffer(UMGRSCommandBuffer* CmdBuf);

private:
    mg-rs::Context* Context;
    int32 SelectedDeviceIndex;
};
```

### UMGRSBuffer

```cpp
class UMGRSBuffer : public UObject {
    GENERATED_BODY()

public:
    // Data access
    void WriteData(const TArray<uint8>& Data);
    void ReadData(TArray<uint8>& OutData);

    // GPU operations
    void UploadToGPU();
    void DownloadFromGPU();

    // Memory management
    void Map();
    void Unmap();

    // Buffer properties
    int32 GetSize() const;
    EBufferUsage GetUsage() const;

private:
    mg-rs::Buffer* Buffer;
    void* MappedPointer;
};
```

### UMGRSImage

```cpp
class UMGRSImage : public UObject {
    GENERATED_BODY()

public:
    // Texture operations
    UTexture2D* GetTexture() const;
    void SetTexture(UTexture2D* Texture);

    // GPU operations
    void UploadToGPU();
    void DownloadFromGPU();

    // Image properties
    int32 GetWidth() const;
    int32 GetHeight() const;
    EImageFormat GetFormat() const;
    EImageUsage GetUsage() const;

private:
    mg-rs::Image* Image;
    UTexture2D* Texture;
};
```

### UMGRSCommandBuffer

```cpp
class UMGRSCommandBuffer : public UObject {
    GENERATED_BODY()

public:
    // Command buffer management
    void BeginRecording();
    void EndRecording();

    // Draw commands
    void Draw(int32 VertexCount, int32 InstanceCount);

    // Compute commands
    void Dispatch(int32 GroupCountX, int32 GroupCountY, int32 GroupCountZ);

    // Resource operations
    void TransitionImageLayout(UMGRSImage* Image, EImageLayout OldLayout, EImageLayout NewLayout);
    void CopyBufferToImage(UMGRSBuffer* Buffer, UMGRSImage* Image);

private:
    mg-rs::CommandBuffer* CmdBuf;
};
```

### UMGRSBlueprintFunctionLibrary

```cpp
UCLASS()
class UMGRSBlueprintFunctionLibrary : public UBlueprintFunctionLibrary {
    GENERATED_BODY()

public:
    // Context creation
    UFUNCTION(BlueprintPure, Category = "MGRS")
    static AMGRSContext* GetContext();

    // Resource creation
    UFUNCTION(BlueprintPure, Category = "MGRS|Resources")
    static UMGRSBuffer* CreateBuffer(int32 Size, EBufferUsage Usage);

    UFUNCTION(BlueprintPure, Category = "MGRS|Resources")
    static UMGRSImage* CreateImage(int32 Width, int32 Height, EImageFormat Format, EImageUsage Usage);

    // Command buffer management
    UFUNCTION(BlueprintPure, Category = "MGRS|Commands")
    static UMGRSCommandBuffer* CreateCommandBuffer();

    UFUNCTION(BlueprintCallable, Category = "MGRS|Commands")
    static void SubmitCommandBuffer(UMGRSCommandBuffer* CmdBuf);
};
```

## Integration Points

### Unreal Engine 5 Renderer Integration

```cpp
class FMGRSRendererModule : public IModuleInterface {
public:
    virtual void StartupModule() override;
    virtual void ShutdownModule() override;

private:
    // Render thread functions
    void OnPreRender();
    void OnPostRender();
    void OnBeginFrame();
    void OnEndFrame();

    // Renderer integration
    void RegisterRendererInterface();
    void UnregisterRendererInterface();

    FDelegateHandle PreRenderHandle;
    FDelegateHandle PostRenderHandle;
    FDelegateHandle BeginFrameHandle;
    FDelegateHandle EndFrameHandle;
};
```

### Material Shader Integration

```hlsl
// Custom material shader for mg-rs
void Main(
    in float4 InPosition : POSITION,
    in float4 InColor : COLOR,
    out float4 OutPosition : SV_POSITION,
    out float4 OutColor : COLOR0)
{
    OutPosition = InPosition;
    OutColor = InColor;
}
```

## Blueprint Usage

```blueprint
// Create a buffer
MyBuffer = MGRSBlueprintFunctionLibrary.CreateBuffer(1024 * 1024, EBufferUsage::UniformBuffer)

// Write data
MyBuffer.WriteData(MyData)

// Upload to GPU
MyBuffer.UploadToGPU()

// Create command buffer
MyCmdBuf = MGRSBlueprintFunctionLibrary.CreateCommandBuffer()

// Record commands
MyCmdBuf.BeginRecording()
MyCmdBuf.Draw(3, 1)
MyCmdBuf.EndRecording()

// Submit command buffer
MGRSBlueprintFunctionLibrary.SubmitCommandBuffer(MyCmdBuf)
```

## Performance Optimizations

### Command Buffer Reuse

```cpp
// Reuse command buffers for frequently used commands
UMGRSCommandBuffer* GetCachedCommandBuffer() {
    static TArray<UMGRSCommandBuffer*> CachedCmdBufs;
    if (CachedCmdBufs.Num() > 0) {
        return CachedCmdBufs.Pop();
    }
    return MGRSBlueprintFunctionLibrary.CreateCommandBuffer();
}

void ReturnCachedCommandBuffer(UMGRSCommandBuffer* CmdBuf) {
    static TArray<UMGRSCommandBuffer*> CachedCmdBufs;
    CachedCmdBufs.Add(CmdBuf);
}
```

### Asynchronous Resource Upload

```cpp
// Async resource upload
void AsyncUploadResource(UMGRSResource* Resource) {
    AsyncTask(ENamedThreads::AnyBackgroundThreadNormalTask, [Resource]() {
        Resource->UploadToGPU();
    });
}
```

## Future Enhancements

### Ray Tracing Integration

```cpp
// Ray tracing pipeline creation
UMGRSRayTracingPipeline* CreateRayTracingPipeline();

// Ray tracing commands
void TraceRays(int32 Width, int32 Height);

// Ray tracing intersection testing
bool TraceRay(const FVector& Start, const FVector& Direction, float MaxDistance, FHitResult& Hit);
```

### AI/ML Integration

```cpp
// AI inference command buffer
void RunInference(UMGRSBuffer* Input, UMGRSBuffer* Output, const FString& ModelPath);

// AI-generated content creation
UMGRSImage* GenerateTexture(const FString& Prompt);
```

### VR/AR Support

```cpp
// VR eye tracking integration
void SetEyeTrackingData(const FEyeTrackingData& Data);

// VR hand tracking integration
void SetHandTrackingData(int32 HandIndex, const FHandTrackingData& Data);
```
