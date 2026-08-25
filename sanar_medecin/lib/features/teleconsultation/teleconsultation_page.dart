import 'package:flutter/material.dart';
import 'package:flutter_webrtc/flutter_webrtc.dart';
import '../../../core/constants/app_colors.dart';

/// Page de teleconsultation WebRTC audio/video.
/// Demarre la camera locale + invite a rejoindre une room via signaling.
class TeleconsultationPage extends StatefulWidget {
  final String? roomId;

  const TeleconsultationPage({super.key, this.roomId});

  @override
  State<TeleconsultationPage> createState() => _TeleconsultationPageState();
}

class _TeleconsultationPageState extends State<TeleconsultationPage> {
  final RTCVideoRenderer _localRenderer = RTCVideoRenderer();
  final RTCVideoRenderer _remoteRenderer = RTCVideoRenderer();
  MediaStream? _localStream;
  RTCPeerConnection? _peerConnection;
  bool _micEnabled = true;
  bool _cameraEnabled = true;
  bool _connected = false;
  bool _initializing = true;

  @override
  void initState() {
    super.initState();
    _initRenderers();
  }

  Future<void> _initRenderers() async {
    await _localRenderer.initialize();
    await _remoteRenderer.initialize();
    await _startLocalStream();
    if (mounted) setState(() => _initializing = false);
  }

  Future<void> _startLocalStream() async {
    try {
      final mediaConstraints = <String, dynamic>{
        'audio': true,
        'video': {
          'facingMode': 'user',
          'width': 640,
          'height': 480,
        },
      };
      _localStream =
          await navigator.mediaDevices.getUserMedia(mediaConstraints);
      _localRenderer.srcObject = _localStream;
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Erreur camera/micro : $e'),
            backgroundColor: AppColors.danger,
          ),
        );
      }
    }
  }

  Future<void> _toggleMic() async {
    if (_localStream == null) return;
    final audioTracks = _localStream!.getAudioTracks();
    for (final t in audioTracks) {
      t.enabled = !_micEnabled;
    }
    setState(() => _micEnabled = !_micEnabled);
  }

  Future<void> _toggleCamera() async {
    if (_localStream == null) return;
    final videoTracks = _localStream!.getVideoTracks();
    for (final t in videoTracks) {
      t.enabled = !_cameraEnabled;
    }
    setState(() => _cameraEnabled = !_cameraEnabled);
  }

  Future<void> _connect() async {
    // La logique de signaling (websocket / SSE / REST) doit etre branchee ici.
    // On simule la connexion pour le PPE.
    setState(() => _connected = true);
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Connexion en cours... En attente du patient.'),
      ),
    );
  }

  Future<void> _hangUp() async {
    await _localStream?.dispose();
    await _peerConnection?.close();
    if (mounted) {
      Navigator.pop(context);
    }
  }

  @override
  void dispose() {
    _localStream?.dispose();
    _peerConnection?.close();
    _localRenderer.dispose();
    _remoteRenderer.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        title: Text(widget.roomId != null
            ? 'Teleconsultation #${widget.roomId}'
            : 'Teleconsultation'),
      ),
      body: _initializing
          ? const Center(
              child: CircularProgressIndicator(color: Colors.white),
            )
          : Stack(
              children: [
                // Flux distant (plein ecran)
                Positioned.fill(
                  child: RTCVideoView(
                    _remoteRenderer,
                    objectFit: RTCVideoViewObjectFit.RTCVideoViewObjectFitContain,
                  ),
                ),
                if (!_connected)
                  const Center(
                    child: Padding(
                      padding: EdgeInsets.all(24),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.videocam_off_outlined,
                              color: Colors.white70, size: 56),
                          SizedBox(height: 12),
                          Text(
                            'Patient non connecte',
                            style: TextStyle(color: Colors.white70, fontSize: 16),
                            textAlign: TextAlign.center,
                          ),
                          SizedBox(height: 8),
                          Text(
                            'Cliquez sur "Appeler" pour lancer la teleconsultation.',
                            style: TextStyle(color: Colors.white54, fontSize: 13),
                            textAlign: TextAlign.center,
                          ),
                        ],
                      ),
                    ),
                  ),
                // Flux local (miniature)
                Positioned(
                  right: 16,
                  top: 16,
                  child: Container(
                    width: 110,
                    height: 150,
                    decoration: BoxDecoration(
                      color: Colors.black54,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: Colors.white30),
                    ),
                    clipBehavior: Clip.hardEdge,
                    child: RTCVideoView(
                      _localRenderer,
                      mirror: true,
                      objectFit:
                          RTCVideoViewObjectFit.RTCVideoViewObjectFitCover,
                    ),
                  ),
                ),
                // Barre de controles
                Positioned(
                  left: 0,
                  right: 0,
                  bottom: 24,
                  child: Center(
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 16, vertical: 10),
                      decoration: BoxDecoration(
                        color: Colors.black.withOpacity(0.5),
                        borderRadius: BorderRadius.circular(40),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          _controlButton(
                            icon: _micEnabled
                                ? Icons.mic
                                : Icons.mic_off,
                            color: _micEnabled
                                ? Colors.white
                                : AppColors.danger,
                            onTap: _toggleMic,
                          ),
                          const SizedBox(width: 12),
                          _controlButton(
                            icon: _cameraEnabled
                                ? Icons.videocam
                                : Icons.videocam_off,
                            color: _cameraEnabled
                                ? Colors.white
                                : AppColors.danger,
                            onTap: _toggleCamera,
                          ),
                          const SizedBox(width: 12),
                          if (!_connected)
                            _controlButton(
                              icon: Icons.call,
                              color: AppColors.accent,
                              onTap: _connect,
                            )
                          else
                            _controlButton(
                              icon: Icons.call_end,
                              color: AppColors.danger,
                              onTap: _hangUp,
                            ),
                        ],
                      ),
                    ),
                  ),
                ),
              ],
            ),
    );
  }

  Widget _controlButton({
    required IconData icon,
    required Color color,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(24),
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: color,
          shape: BoxShape.circle,
        ),
        child: Icon(icon, color: Colors.white),
      ),
    );
  }
}
