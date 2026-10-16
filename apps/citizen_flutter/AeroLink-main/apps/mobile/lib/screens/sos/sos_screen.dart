import 'dart:convert';

import 'sos_chat_screen.dart';
import 'widgets/sos_completion_listener.dart';

import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';

import '../more/more_screen.dart';
import '../home/home_screen.dart';

import '../../widgets/app_bottom_navigation.dart';

import 'widgets/sos_status_card.dart';
import 'widgets/sos_action_button.dart';
import 'widgets/emergency_conditions.dart';
import 'widgets/additional_details.dart';
import 'widgets/sos_information_card.dart';
import 'widgets/sos_transmission_stage_card.dart';

import '../../services/location_service.dart';
import '../../services/ble_service.dart';
import '../../services/sos_service.dart';
import '../../services/communication_service.dart';
import '../../services/lakhimpur_service.dart';
import '../../l10n/app_localizations.dart';

class SOSScreen extends StatefulWidget {
  const SOSScreen({super.key});

  @override
  State<SOSScreen> createState() => _SOSScreenState();
}

class _SOSScreenState extends State<SOSScreen> {
  final LocationService _locationService = LocationService();

  final BleService _bleService = BleService.instance;
  final SOSService _sosService = SOSService.instance;

  // ==========================================
  // EMERGENCY READINESS
  // ==========================================

  Position? _currentPosition;

  bool _locationReady = false;
  bool _transmissionReady = false;
  bool _isChecking = true;

  // ==========================================
  // LIVE REPORT FORM STATE
  // ==========================================

  int _peopleAffected = 1;
  Set<EmergencyCondition> _conditions = {};
  final TextEditingController _detailsController = TextEditingController();

  String _selectedIncidentType = 'rescue_sos';
  String _selectedRoadStatus = 'blocked';
  double _waterDepthCm = 45.0;
  String _waterTrend = 'rising';
  SettlementInfo? _selectedSettlement;
  String _currentApiUrl = 'http://10.10.0.170:8000';

  @override
  void initState() {
    super.initState();

    LakhimpurDistrictService.instance.getApiUrl().then((url) {
      if (mounted) setState(() => _currentApiUrl = url);
    });

    // Listen to SOS stage changes.
    _sosService.addListener(_onSOSServiceChanged);

    _bleService.addListener(_onBleChanged);
    _checkEmergencyReadiness();
  }

  void _onBleChanged() {
    if (mounted) setState(() => _transmissionReady = _bleService.isConnected);
  }

  void _onSOSServiceChanged() {
    if (mounted) {
      setState(() {});
    }
  }

  @override
  void dispose() {
    _sosService.removeListener(_onSOSServiceChanged);
    _bleService.removeListener(_onBleChanged);

    _detailsController.dispose();

    super.dispose();
  }

  // ==========================================
  // EMERGENCY READINESS
  // ==========================================

  Future<void> _checkEmergencyReadiness() async {
    if (mounted) {
      setState(() {
        _isChecking = true;
      });
    }

    await Future.wait([_checkLocation(), _checkTransmission()]);

    if (!mounted) return;

    setState(() {
      _isChecking = false;
    });
  }

  Future<void> _checkLocation() async {
    try {
      final Position position = await _locationService.getCurrentPosition();

      if (!mounted) return;

      setState(() {
        _currentPosition = position;
        _locationReady = true;
        _selectedSettlement ??= LakhimpurDistrictService.instance.snapNearestSettlement(
          position.latitude,
          position.longitude,
        );
      });
    } catch (_) {
      if (!mounted) return;

      setState(() {
        _locationReady = false;
        _selectedSettlement ??= LakhimpurDistrictService.settlements.first;
      });
    }
  }

  Future<void> _checkTransmission() async {
    _onBleChanged();
    final bool hasInternet = await CommunicationService().checkInternetConnection();
    if (mounted) {
      setState(() {
        _transmissionReady = _bleService.isConnected || hasInternet;
      });
    }
  }

  // ==========================================
  // CREATE LIVE REPORT JSON
  // ==========================================

  String _createSOSJson() {
    final nearest = _selectedSettlement ??
        LakhimpurDistrictService.instance.snapNearestSettlement(
          _currentPosition?.latitude,
          _currentPosition?.longitude,
        ) ??
        LakhimpurDistrictService.settlements.first;

    final sosData = {
      'type': _selectedIncidentType == 'rescue_sos' ? 'SOS' : _selectedIncidentType,
      'incidentType': _selectedIncidentType,
      'timestamp': DateTime.now().toUtc().toIso8601String(),
      'latitude': _currentPosition?.latitude ?? nearest.coordinates.latitude,
      'longitude': _currentPosition?.longitude ?? nearest.coordinates.longitude,
      'settlementId': nearest.id,
      'settlementName': nearest.name,
      'peopleAffected': _peopleAffected,
      'roadStatus': _selectedIncidentType == 'road_closure' ? _selectedRoadStatus : null,
      'waterDepthCm': _selectedIncidentType == 'flood_rising' ? _waterDepthCm : null,
      'waterTrend': _selectedIncidentType == 'flood_rising' ? _waterTrend : null,
      'conditions': _conditions.map((condition) => condition.name).toList(),
      'additionalDetails': _detailsController.text.trim(),
    };

    return jsonEncode(sosData);
  }

  // ==========================================
  // SOS ACTIVATION
  // ==========================================

  Future<void> _handleSOSActivation() async {
    if (_sosService.isTransmitting) {
      return;
    }

    try {
      await _sosService.sendSOS(_createSOSJson());
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(error.toString().replaceFirst('Exception: ', '')),
        ),
      );
    }
  }

  // ==========================================
  // RETRY
  // ==========================================

  Future<void> _retrySOS() => _sosService.retry();

  // ==========================================
  // RESET
  // ==========================================

  void _resetSOS() {
    _sosService.reset(force: true);

    setState(() {
      _peopleAffected = 1;
      _conditions = {};
      _selectedIncidentType = 'rescue_sos';
      _detailsController.clear();
    });
  }

  void _showServerConfigDialog() {
    final controller = TextEditingController(text: _currentApiUrl);
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Control Center Server URL'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Enter the backend URL (e.g. http://10.10.0.170:8000 or http://10.10.0.170:8001):',
              style: TextStyle(fontSize: 12),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: controller,
              decoration: const InputDecoration(
                border: OutlineInputBorder(),
                hintText: 'http://10.10.0.170:8000',
              ),
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          FilledButton(
            onPressed: () async {
              final newUrl = controller.text.trim();
              if (newUrl.isNotEmpty) {
                await LakhimpurDistrictService.instance.setApiUrl(newUrl);
                if (mounted) {
                  setState(() => _currentApiUrl = newUrl);
                }
              }
              if (ctx.mounted) Navigator.pop(ctx);
            },
            child: const Text('Save & Test'),
          ),
        ],
      ),
    );
  }

  // ==========================================
  // VOICE INPUT
  // ==========================================

  void _startVoiceInput() {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(AppLocalizations.of(context)!.voiceInputComingSoon),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final bool showingTransmissionStage = _sosService.stage != SOSStage.idle;

    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            // ==========================================
            // HEADER
            // ==========================================

            Container(
              width: double.infinity,
              decoration: BoxDecoration(
                color: Colors.white,
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: 0.06),
                    blurRadius: 10,
                    offset: const Offset(0, 3),
                  ),
                ],
              ),
              child: SizedBox(
                height: 56,
                child: Stack(
                  alignment: Alignment.center,
                  children: [
                    Positioned(
                      left: 8,
                      child: IconButton(
                        onPressed: () {
                          Navigator.pop(context);
                        },
                        icon: const Icon(Icons.arrow_back_rounded, size: 22),
                      ),
                    ),

                    const Text(
                      'Live Field Report · Lakhimpur',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.w700,
                        color: Colors.black87,
                      ),
                    ),
                  ],
                ),
              ),
            ),

            // ==========================================
            // MAIN CONTENT
            // ==========================================
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(16),

                child: AnimatedSwitcher(
                  duration: const Duration(milliseconds: 350),

                  child: showingTransmissionStage
                      ? _buildTransmissionStage()
                      : _buildSOSForm(),
                ),
              ),
            ),
          ],
        ),
      ),

      // ==========================================
      // BOTTOM NAVIGATION
      // ==========================================
      bottomNavigationBar: AppBottomNavigation(
        currentIndex: 1,

        onHome: () {
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(builder: (_) => const HomeScreen()),
          );
        },

        onSOS: () {
          // Already on SOS.
        },

        onMore: () {
          Navigator.pushReplacement(
            context,
            MaterialPageRoute(builder: (_) => const MoreScreen()),
          );
        },
      ),
    );
  }

  // ==========================================
  // SOS FORM
  // ==========================================

  Widget _buildSOSForm() {
    return Column(
      key: const ValueKey('sos_form'),
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          'Lakhimpur Flood Response · Real-time ground report with AI prioritization and mesh fallback',
          textAlign: TextAlign.center,
          style: TextStyle(fontSize: 12, height: 1.5, color: Colors.grey[600]),
        ),

        const SizedBox(height: 12),

        // Server Connection Indicator Chip
        Center(
          child: InkWell(
            onTap: _showServerConfigDialog,
            borderRadius: BorderRadius.circular(20),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: const Color(0xFFF0FDF4),
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: const Color(0xFF86EFAC)),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.dns_rounded, size: 14, color: Color(0xFF15803D)),
                  const SizedBox(width: 6),
                  Text(
                    'Control Center: $_currentApiUrl',
                    style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: Color(0xFF15803D)),
                  ),
                  const SizedBox(width: 4),
                  const Icon(Icons.edit, size: 12, color: Color(0xFF15803D)),
                ],
              ),
            ),
          ),
        ),

        const SizedBox(height: 14),

        // Incident Category Selector
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: Colors.grey[50],
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: Colors.grey[200]!),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Report Category',
                style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 10),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  _categoryChip('rescue_sos', '🚨 Rescue SOS', Colors.red),
                  _categoryChip('road_closure', '⛔ Road Block', Colors.amber[800]!),
                  _categoryChip('flood_rising', '🌊 Water Rising', Colors.blue),
                  _categoryChip('medical', '🏥 Medical Need', Colors.purple),
                  _categoryChip('general', '⚠️ General Report', Colors.blueGrey),
                ],
              ),
            ],
          ),
        ),

        const SizedBox(height: 14),

        // Road status contextual options
        if (_selectedIncidentType == 'road_closure') ...[
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.amber[50],
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.amber[300]!),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Road Status Observation',
                  style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Colors.brown),
                ),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  children: [
                    _choiceChip('blocked', 'Completely Blocked', _selectedRoadStatus, (v) => setState(() => _selectedRoadStatus = v)),
                    _choiceChip('partially_blocked', 'Partially Passable', _selectedRoadStatus, (v) => setState(() => _selectedRoadStatus = v)),
                    _choiceChip('open', 'Submerged but Open', _selectedRoadStatus, (v) => setState(() => _selectedRoadStatus = v)),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 14),
        ],

        // Water trend contextual options
        if (_selectedIncidentType == 'flood_rising') ...[
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.blue[50],
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.blue[200]!),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Water Ingress Trend',
                  style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: Colors.indigo),
                ),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  children: [
                    _choiceChip('rising', 'Rising Fast ⬆️', _waterTrend, (v) => setState(() => _waterTrend = v)),
                    _choiceChip('stable', 'Stable / Stagnant ⏸️', _waterTrend, (v) => setState(() => _waterTrend = v)),
                    _choiceChip('falling', 'Receding ⬇️', _waterTrend, (v) => setState(() => _waterTrend = v)),
                  ],
                ),
                const SizedBox(height: 10),
                const Text(
                  'Estimated Water Depth',
                  style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Colors.indigo),
                ),
                const SizedBox(height: 6),
                Wrap(
                  spacing: 8,
                  children: [
                    _depthChip(15.0, 'Ankle (15 cm)'),
                    _depthChip(45.0, 'Knee (45 cm)'),
                    _depthChip(90.0, 'Waist (90 cm)'),
                    _depthChip(150.0, 'Chest+ (150 cm)'),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 14),
        ],

        // Settlement Selector for Lakhimpur
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: Colors.grey[300]!),
          ),
          child: Row(
            children: [
              const Icon(Icons.location_on, color: Color(0xFFFF6B35), size: 20),
              const SizedBox(width: 8),
              const Text('Village: ', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
              Expanded(
                child: DropdownButtonHideUnderline(
                  child: DropdownButton<SettlementInfo>(
                    value: _selectedSettlement ?? LakhimpurDistrictService.settlements.first,
                    isExpanded: true,
                    items: LakhimpurDistrictService.settlements.map((s) {
                      return DropdownMenuItem(
                        value: s,
                        child: Text(s.name, style: const TextStyle(fontSize: 13)),
                      );
                    }).toList(),
                    onChanged: (s) {
                      if (s != null) setState(() => _selectedSettlement = s);
                    },
                  ),
                ),
              ),
            ],
          ),
        ),

        const SizedBox(height: 16),

        SOSStatusCard(
          locationReady: _locationReady,
          transmissionReady: _transmissionReady,
        ),

        if (_isChecking) ...[
          const SizedBox(height: 8),
          const Text(
            'Checking field readiness…',
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 12, color: Colors.grey),
          ),
        ],

        const SizedBox(height: 14),

        SOSInformationCard(
          peopleAffected: _peopleAffected,
          onPeopleAffectedChanged: (count) {
            setState(() {
              _peopleAffected = count;
            });
          },
          selectedConditions: _conditions,
          onConditionsChanged: (conditions) {
            setState(() {
              _conditions = conditions;
            });
          },
        ),

        const SizedBox(height: 20),

        AdditionalDetails(
          controller: _detailsController,
          onVoicePressed: _startVoiceInput,
        ),

        const SizedBox(height: 24),

        SOSActionButton(onActivate: _handleSOSActivation),

        const SizedBox(height: 12),

        Text(
          'Hold to transmit live report to Lakhimpur Control Center',
          textAlign: TextAlign.center,
          style: TextStyle(fontSize: 12, color: Colors.grey[500]),
        ),

        const SizedBox(height: 24),
      ],
    );
  }

  Widget _categoryChip(String type, String label, Color color) {
    final selected = _selectedIncidentType == type;
    return ChoiceChip(
      label: Text(label),
      selected: selected,
      selectedColor: color.withValues(alpha: 0.18),
      side: BorderSide(color: selected ? color : Colors.grey[300]!),
      labelStyle: TextStyle(
        fontSize: 12,
        fontWeight: selected ? FontWeight.bold : FontWeight.normal,
        color: selected ? color : Colors.black87,
      ),
      onSelected: (_) => setState(() => _selectedIncidentType = type),
    );
  }

  Widget _choiceChip(String value, String label, String current, ValueChanged<String> onSelect) {
    final selected = current == value;
    return ChoiceChip(
      label: Text(label),
      selected: selected,
      labelStyle: TextStyle(
        fontSize: 11,
        fontWeight: selected ? FontWeight.bold : FontWeight.normal,
      ),
      onSelected: (_) => onSelect(value),
    );
  }

  Widget _depthChip(double val, String label) {
    final selected = _waterDepthCm == val;
    return ChoiceChip(
      label: Text(label),
      selected: selected,
      labelStyle: TextStyle(
        fontSize: 11,
        fontWeight: selected ? FontWeight.bold : FontWeight.normal,
      ),
      onSelected: (_) => setState(() => _waterDepthCm = val),
    );
  }

  // ==========================================
  // TRANSMISSION STAGE
  // ==========================================

  Widget _buildTransmissionStage() {
    return Column(
      key: const ValueKey('transmission_stage'),

      children: [
        const SizedBox(height: 24),

        SOSTransmissionStageCard(
          service: _sosService,

          onChat: () => Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => SOSChatScreen(service: _sosService),
            ),
          ),
          onReviewCompletion: () =>
              showSOSCompletionDialog(context, _sosService),

          onRetry: _retrySOS,

          onReset: _resetSOS,
        ),

        const SizedBox(height: 24),
      ],
    );
  }
}
