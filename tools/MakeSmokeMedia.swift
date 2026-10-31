import Foundation
import ImageIO
import UniformTypeIdentifiers
import AVFoundation
import CoreGraphics

@main struct MakeSmokeMedia {
 static func main() async throws {
  let folder = URL(fileURLWithPath: CommandLine.arguments[1])
  precondition(!FileManager.default.fileExists(atPath: folder.path), "Use a new fixture directory")
  try FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
  let width=640, height=480
  let context=CGContext(data:nil,width:width,height:height,bitsPerComponent:8,bytesPerRow:0,space:CGColorSpaceCreateDeviceRGB(),bitmapInfo:CGImageAlphaInfo.noneSkipLast.rawValue)!
  context.setFillColor(CGColor(red:0.1,green:0.5,blue:0.8,alpha:1));context.fill(CGRect(x:0,y:0,width:width,height:height))
  context.setFillColor(CGColor(red:0.9,green:0.7,blue:0.2,alpha:1));context.fillEllipse(in:CGRect(x:100,y:100,width:200,height:200))
  let image=context.makeImage()!
  for (name,type) in [("pilot.png",UTType.png),("pilot.jpg",UTType.jpeg),("pilot.heic",UTType.heic)] {
   let dest=CGImageDestinationCreateWithURL(folder.appendingPathComponent(name) as CFURL,type.identifier as CFString,1,nil)!
   CGImageDestinationAddImage(dest,image,nil);precondition(CGImageDestinationFinalize(dest))
  }
  let writer=try AVAssetWriter(outputURL:folder.appendingPathComponent("motion.mov"),fileType:.mov)
  let input=AVAssetWriterInput(mediaType:.video,outputSettings:[AVVideoCodecKey:AVVideoCodecType.h264,AVVideoWidthKey:320,AVVideoHeightKey:240])
  let adapter=AVAssetWriterInputPixelBufferAdaptor(assetWriterInput:input,sourcePixelBufferAttributes:[kCVPixelBufferPixelFormatTypeKey as String:kCVPixelFormatType_32BGRA,kCVPixelBufferWidthKey as String:320,kCVPixelBufferHeightKey as String:240])
  writer.add(input);precondition(writer.startWriting());writer.startSession(atSourceTime:.zero)
  for i in 0..<30 {
   while !input.isReadyForMoreMediaData { try await Task.sleep(nanoseconds:1_000_000) }
   var buffer:CVPixelBuffer?;precondition(CVPixelBufferPoolCreatePixelBuffer(nil,adapter.pixelBufferPool!,&buffer)==kCVReturnSuccess)
   CVPixelBufferLockBaseAddress(buffer!,[])
   let c=CGContext(data:CVPixelBufferGetBaseAddress(buffer!),width:320,height:240,bitsPerComponent:8,bytesPerRow:CVPixelBufferGetBytesPerRow(buffer!),space:CGColorSpaceCreateDeviceRGB(),bitmapInfo:CGImageAlphaInfo.premultipliedFirst.rawValue|CGBitmapInfo.byteOrder32Little.rawValue)!
   c.setFillColor(CGColor(red:Double(i)/30,green:0.4,blue:0.8,alpha:1));c.fill(CGRect(x:0,y:0,width:320,height:240))
   CVPixelBufferUnlockBaseAddress(buffer!,[]);precondition(adapter.append(buffer!,withPresentationTime:CMTime(value:Int64(i),timescale:30)))
  }
  input.markAsFinished();await writer.finishWriting();precondition(writer.status == .completed)
 }
}
