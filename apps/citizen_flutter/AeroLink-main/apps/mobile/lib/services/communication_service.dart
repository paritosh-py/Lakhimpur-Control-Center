import 'package:connectivity_plus/connectivity_plus.dart';

class CommunicationService {
  final Connectivity _connectivity = Connectivity();

  Future<bool> checkInternetConnection() async {
    final List<ConnectivityResult> result = await _connectivity
        .checkConnectivity();

    return !result.contains(ConnectivityResult.none);
  }
}
