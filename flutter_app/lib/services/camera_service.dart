
import 'dart:io';
import 'package:image_picker/image_picker.dart';
import 'package:flutter_image_compress/flutter_image_compress.dart';
import 'package:path_provider/path_provider.dart';
import 'package:path/path.dart' as p;

class CameraService {
  final _picker = ImagePicker();

  /// Captures a photo from the camera and compresses it.
  /// Returns the compressed [File], or null if cancelled/failed.
  Future<File?> takePhoto() async {
    try {
      final XFile? photo = await _picker.pickImage(
        source: ImageSource.camera,
        preferredCameraDevice: CameraDevice.rear,
      );

      if (photo == null) return null;

      final File rawFile = File(photo.path);
      return await _compressImage(rawFile);
    } catch (e) {
      print('Error capturing photo: $e');
      return null;
    }
  }
  
  /// Picks a photo from gallery and compresses it.
  Future<File?> pickFromGallery() async {
    try {
      final XFile? photo = await _picker.pickImage(source: ImageSource.gallery);
      if (photo == null) return null;
      
      return await _compressImage(File(photo.path));
    } catch (e) {
      print('Error picking photo: $e');
      return null;
    }
  }

  Future<File?> _compressImage(File file) async {
    try {
      final dir = await getTemporaryDirectory();
      final targetPath = p.join(dir.path, 'compressed_${DateTime.now().millisecondsSinceEpoch}.jpg');

      var result = await FlutterImageCompress.compressAndGetFile(
        file.absolute.path,
        targetPath,
        quality: 85,
        minWidth: 1024,
        minHeight: 1024,
      );

      return result != null ? File(result.path) : null;
    } catch (e) {
      print('Error compressing image: $e');
      // Return original if compression fails
      return file;
    }
  }
}
