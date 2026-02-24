# Frame Execution Pipeline

## Overview

The frame execution pipeline describes the sequence of operations required to render a single frame using mg-rs.

## Frame Execution Steps

### 1. Begin Frame

```cpp
mg-rs::Context* context = ...;
context->BeginFrame();
```

### 2. Update Game State

```cpp
// Update game logic
game->Update(deltaTime);
```

### 3. Record Commands

```cpp
// Create command buffer
mg-rs::CommandBuffer* cmdBuf = context->CreateCommandBuffer();

// Begin recording
cmdBuf->Begin();

// Record draw commands
cmdBuf->BeginRenderPass(...);
cmdBuf->SetPipeline(...);
cmdBuf->Draw(...);
cmdBuf->EndRenderPass();

// End recording
cmdBuf->End();
```

### 4. Schedule Execution

```cpp
// Create timeline semaphore for synchronization
mg-rs::TimelineSemaphore* sem = context->CreateTimelineSemaphore();

// Schedule command buffer
mg-rs::CommandSubmitInfo submitInfo;
submitInfo.commandBuffer = cmdBuf;
submitInfo.signalSemaphore = sem;
submitInfo.signalValue = 1;

context->SubmitCommandBuffer(submitInfo);
```

### 5. Present Frame

```cpp
// Present to swap chain
mg-rs::SwapChain* swapChain = context->GetSwapChain();
swapChain->Present();
```

### 6. End Frame

```cpp
context->EndFrame();
```

## Timeline Semaphore Usage

```cpp
// Create timeline semaphore with initial value 0
mg-rs::TimelineSemaphore* sem = context->CreateTimelineSemaphore();

// Schedule command buffer with signal value 1
context->SubmitCommandBuffer({ cmdBuf, sem, 1 });

// Wait for semaphore value to reach 1
sem->Wait(1);
```

## Multi-GPU Execution

```cpp
// Submit to specific device
mg-rs::CommandSubmitInfo submitInfo;
submitInfo.commandBuffer = cmdBuf;
submitInfo.deviceIndex = 1; // Second GPU

context->SubmitCommandBuffer(submitInfo);
```

## Async Execution

```cpp
// Submit command buffer without waiting
context->SubmitCommandBuffer(submitInfo);

// Continue with other work

// Wait for completion if needed
sem->Wait(1);
```
