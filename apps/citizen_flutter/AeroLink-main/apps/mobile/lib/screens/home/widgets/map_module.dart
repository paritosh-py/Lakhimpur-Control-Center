import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:geolocator/geolocator.dart';
import 'package:flutter_map_cancellable_tile_provider/flutter_map_cancellable_tile_provider.dart';
import 'package:mobile/l10n/app_localizations.dart';
import '../../../../services/lakhimpur_service.dart';

class MapModule extends StatefulWidget {
  final Position? position;
  final String gpsTimestamp;
  final VoidCallback onRefresh;

  const MapModule({
    super.key,
    required this.position,
    required this.gpsTimestamp,
    required this.onRefresh,
  });

  @override
  State<MapModule> createState() => _MapModuleState();
}

class _MapModuleState extends State<MapModule> {
  final MapController _mapController = MapController();

  static const Color _primaryColor = Color(0xFFFF6B35);

  LatLng get _currentLocation {
    if (widget.position != null) {
      return LatLng(widget.position!.latitude, widget.position!.longitude);
    }

    // Default to Lakhimpur District Center
    return LakhimpurDistrictService.districtCenter;
  }

  @override
  void didUpdateWidget(covariant MapModule oldWidget) {
    super.didUpdateWidget(oldWidget);

    if (widget.position != null) {
      final newPosition = widget.position!;
      final oldPosition = oldWidget.position;

      final hasPositionChanged =
          oldPosition == null ||
          newPosition.latitude != oldPosition.latitude ||
          newPosition.longitude != oldPosition.longitude;

      if (hasPositionChanged) {
        WidgetsBinding.instance.addPostFrameCallback((_) {
          if (mounted) {
            _mapController.move(
              LatLng(newPosition.latitude, newPosition.longitude),
              16,
            );
          }
        });
      }
    }
  }

  void _recenterMap() {
    if (widget.position != null) {
      _mapController.move(
        LatLng(widget.position!.latitude, widget.position!.longitude),
        16,
      );
    } else {
      _mapController.move(
        LakhimpurDistrictService.districtCenter,
        11,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final hasLocation = widget.position != null;
    final l10n = AppLocalizations.of(context)!;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Section title
        Row(
          children: [
            const SizedBox(width: 8),

            Text(
              l10n.liveLocation,
              style: const TextStyle(
                fontSize: 17,
                fontWeight: FontWeight.w700,
                color: Colors.black87,
              ),
            ),
          ],
        ),

        const SizedBox(height: 12),

        // MAP CARD
        Container(
          height: 250,
          width: double.infinity,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(22),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.10),
                blurRadius: 16,
                offset: const Offset(0, 6),
              ),
            ],
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(22),
            child: Stack(
              children: [
                // MAP
                Positioned.fill(
                  child: FlutterMap(
                    mapController: _mapController,
                    options: MapOptions(
                      initialCenter: _currentLocation,
                      initialZoom: hasLocation ? 16 : 11,
                      interactionOptions: const InteractionOptions(
                        flags: InteractiveFlag.all & ~InteractiveFlag.rotate,
                      ),
                    ),
                    children: [
                      // OpenStreetMap
                      TileLayer(
                        urlTemplate:
                            'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                        userAgentPackageName: 'com.example.aerolink',
                        tileProvider: CancellableNetworkTileProvider(),
                      ),

                      // Lakhimpur District Markers
                      MarkerLayer(
                        markers: [
                          // Basecamp Borimuri HQ
                          Marker(
                            point: LakhimpurDistrictService.basecampBorimuri,
                            width: 104,
                            height: 28,
                            child: Container(
                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                              decoration: BoxDecoration(
                                color: const Color(0xFF1D4ED8),
                                borderRadius: BorderRadius.circular(10),
                                border: Border.all(color: Colors.white, width: 1.5),
                                boxShadow: const [BoxShadow(color: Colors.black38, blurRadius: 4)],
                              ),
                              child: const Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Icon(Icons.flag_rounded, color: Colors.white, size: 13),
                                  SizedBox(width: 4),
                                  Text(
                                    'HQ Borimuri',
                                    style: TextStyle(
                                      color: Colors.white,
                                      fontSize: 10,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),

                          // 16 Study Settlements
                          ...LakhimpurDistrictService.settlements.map(
                            (s) => Marker(
                              point: s.coordinates,
                              width: 76,
                              height: 22,
                              child: Container(
                                padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
                                decoration: BoxDecoration(
                                  color: Colors.white.withValues(alpha: 0.92),
                                  borderRadius: BorderRadius.circular(4),
                                  border: Border.all(color: const Color(0xFF64748B), width: 0.8),
                                ),
                                child: Text(
                                  s.name,
                                  style: const TextStyle(
                                    fontSize: 8.5,
                                    fontWeight: FontWeight.w600,
                                    color: Color(0xFF0F172A),
                                  ),
                                  overflow: TextOverflow.ellipsis,
                                  textAlign: TextAlign.center,
                                ),
                              ),
                            ),
                          ),

                          // Current GPS Location marker
                          if (hasLocation)
                            Marker(
                              point: _currentLocation,
                              width: 64,
                              height: 64,
                              child: const _LocationMarker(),
                            ),
                        ],
                      ),
                    ],
                  ),
                ),

                // TOP LIVE BADGE
                Positioned(
                  top: 14,
                  left: 14,
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 7,
                    ),
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.95),
                      borderRadius: BorderRadius.circular(20),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withValues(alpha: 0.12),
                          blurRadius: 8,
                          offset: const Offset(0, 3),
                        ),
                      ],
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Container(
                          width: 8,
                          height: 8,
                          decoration: BoxDecoration(
                            color: hasLocation ? Colors.green : Colors.orange,
                            shape: BoxShape.circle,
                          ),
                        ),

                        const SizedBox(width: 7),

                        Text(
                          hasLocation ? l10n.liveGps : l10n.locating,
                          style: const TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w700,
                            letterSpacing: 0.8,
                            color: Colors.black87,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),

                // RECENTER BUTTON
                Positioned(
                  right: 14,
                  top: 14,
                  child: Material(
                    color: Colors.white,
                    elevation: 4,
                    borderRadius: BorderRadius.circular(14),
                    child: InkWell(
                      borderRadius: BorderRadius.circular(14),
                      onTap: hasLocation ? _recenterMap : null,
                      child: Container(
                        width: 44,
                        height: 44,
                        alignment: Alignment.center,
                        child: Icon(
                          Icons.my_location_rounded,
                          size: 24,
                          color: hasLocation ? _primaryColor : Colors.grey,
                        ),
                      ),
                    ),
                  ),
                ),

                // BOTTOM GRADIENT
                Positioned(
                  left: 0,
                  right: 0,
                  bottom: 0,
                  height: 60,
                  child: IgnorePointer(
                    child: Container(
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          begin: Alignment.topCenter,
                          end: Alignment.bottomCenter,
                          colors: [
                            Colors.transparent,
                            Colors.black.withValues(alpha: 0.65),
                          ],
                        ),
                      ),
                    ),
                  ),
                ),

                // LOCATION INFO
                Positioned(
                  left: 16,
                  bottom: 14,
                  right: 16,
                  child: Row(
                    children: [
                      Container(
                        width: 36,
                        height: 36,
                        decoration: BoxDecoration(
                          color: _primaryColor,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: const Icon(
                          Icons.location_on_rounded,
                          color: Colors.white,
                          size: 20,
                        ),
                      ),

                      const SizedBox(width: 10),

                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              hasLocation
                                  ? l10n.currentLocation
                                  : l10n.waitingForGps,
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 13,
                                fontWeight: FontWeight.w700,
                              ),
                            ),

                            const SizedBox(height: 2),

                            Text(
                              hasLocation
                                  ? '${widget.position!.latitude.toStringAsFixed(5)}, '
                                        '${widget.position!.longitude.toStringAsFixed(5)}'
                                  : l10n.locationUnavailable,
                              style: TextStyle(
                                color: Colors.white.withValues(alpha: 0.85),
                                fontSize: 11,
                                fontFamily: 'RobotoMono',
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),

                // GPS NOT AVAILABLE OVERLAY
                if (!hasLocation)
                  Positioned.fill(
                    child: Container(
                      color: Colors.white.withValues(alpha: 0.35),
                      child: const Center(
                        child: CircularProgressIndicator(
                          color: _primaryColor,
                          strokeWidth: 3,
                        ),
                      ),
                    ),
                  ),
              ],
            ),
          ),
        ),

        const SizedBox(height: 10),

        // FOOTER
        Row(
          children: [
            Icon(Icons.schedule_rounded, size: 15, color: Colors.grey[600]),

            const SizedBox(width: 6),

            Expanded(
              child: Text(
                widget.gpsTimestamp,
                style: TextStyle(
                  fontSize: 11,
                  color: Colors.grey[600],
                  fontFamily: 'RobotoMono',
                ),
              ),
            ),

            InkWell(
              borderRadius: BorderRadius.circular(10),
              onTap: widget.onRefresh,
              child: Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 10,
                  vertical: 7,
                ),
                decoration: BoxDecoration(
                  color: _primaryColor.withValues(alpha: 0.10),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.refresh_rounded, size: 16, color: _primaryColor),

                    SizedBox(width: 5),

                    Text(
                      l10n.refresh,
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        color: _primaryColor,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ],
    );
  }
}

// ==============================
// CUSTOM LOCATION MARKER
// ==============================

class _LocationMarker extends StatelessWidget {
  const _LocationMarker();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Stack(
        alignment: Alignment.center,
        children: [
          // Outer glow
          Container(
            width: 32,
            height: 32,
            decoration: BoxDecoration(
              color: const Color(0xFFFF6B35).withValues(alpha: 0.20),
              shape: BoxShape.circle,
            ),
          ),

          // Middle circle
          Container(
            width: 16,
            height: 16,
            decoration: BoxDecoration(
              color: Colors.white,
              shape: BoxShape.circle,
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.20),
                  blurRadius: 8,
                ),
              ],
            ),
          ),

          // Actual location dot
          Container(
            width: 12,
            height: 12,
            decoration: const BoxDecoration(
              color: Color(0xFFFF6B35),
              shape: BoxShape.circle,
            ),
          ),
        ],
      ),
    );
  }
}
