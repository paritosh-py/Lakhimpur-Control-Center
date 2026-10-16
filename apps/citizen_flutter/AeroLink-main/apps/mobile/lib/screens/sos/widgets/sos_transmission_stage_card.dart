import 'package:flutter/material.dart';

import '../../../l10n/app_localizations.dart';
import '../../../services/sos_service.dart';
import 'sos_status_card.dart';

class SOSTransmissionStageCard extends StatefulWidget {
  const SOSTransmissionStageCard({
    super.key,
    required this.service,
    required this.onRetry,
    required this.onReset,
    required this.onChat,
    required this.onReviewCompletion,
  });

  final SOSService service;
  final VoidCallback onRetry;
  final VoidCallback onReset;
  final VoidCallback onChat;
  final VoidCallback onReviewCompletion;

  @override
  State<SOSTransmissionStageCard> createState() => _SOSTransmissionStageCardState();
}

class _SOSTransmissionStageCardState extends State<SOSTransmissionStageCard> {
  bool _closing = false;

  Future<void> _handleCloseRequest() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Close this Report?'),
        content: const Text(
          'Mark this incident as resolved/closed on the Lakhimpur Disaster Control Room dashboard?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: const Color(0xFF15803D)),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Confirm Close'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      setState(() => _closing = true);
      final ok = await widget.service.closeOnlineReport();
      if (mounted) {
        setState(() => _closing = false);
        if (ok) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              backgroundColor: Color(0xFF15803D),
              content: Text('✓ Report marked as Closed on the Control Room dashboard.'),
            ),
          );
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              backgroundColor: Colors.red[700],
              content: Text(widget.service.errorMessage ?? 'Could not close report.'),
            ),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (widget.service.isDeliveredOnline || widget.service.stage == SOSStage.completed) {
      return _buildOnlineSuccessCard(context);
    }

    if (widget.service.stage == SOSStage.failed && widget.service.errorMessage != null) {
      return _buildFailureCard(context);
    }

    if (widget.service.deliveryPath != SOSDeliveryPath.mesh) {
      final checking = widget.service.deliveryPath == SOSDeliveryPath.checking;
      return Container(
        margin: const EdgeInsets.symmetric(horizontal: 16),
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: const Color(0xFFCBD5E1)),
        ),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(checking ? 'Checking connection' : 'Sending directly to the dashboard',
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: Color(0xFF0F172A))),
          const SizedBox(height: 12),
          Text(checking
              ? 'Choosing the available delivery connection.'
              : 'Sending over Wi-Fi or mobile data. Waiting for the control center to confirm receipt.',
              style: const TextStyle(color: Color(0xFF475569), height: 1.5)),
          const SizedBox(height: 20),
          const LinearProgressIndicator(),
        ]),
      );
    }

    return _buildOfflineMeshCard(context);
  }

  // ==========================================
  // 1. ONLINE DELIVERY SUCCESS VIEW
  // ==========================================
  Widget _buildOnlineSuccessCard(BuildContext context) {
    final isClosed = widget.service.stage == SOSStage.completed;
    final triage = widget.service.lastTriageResult;
    final urgency = triage?['urgency']?.toString() ?? 'RECEIVED';
    final score = triage?['urgency_score'] ?? 'Unavailable';
    final isCritical = urgency == 'CRITICAL';

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: isClosed ? const Color(0xFF94A3B8) : const Color(0xFF86EFAC), width: 1.5),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.05),
            blurRadius: 16,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Top online delivery indicator
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: isClosed ? const Color(0xFFF1F5F9) : const Color(0xFFDCFCE7),
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  isClosed ? Icons.task_alt_rounded : Icons.check_circle_rounded,
                  color: isClosed ? const Color(0xFF64748B) : const Color(0xFF15803D),
                  size: 26,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      isClosed ? 'REPORT CLOSED / RESOLVED' : 'DELIVERED VIA INTERNET',
                      style: TextStyle(
                        color: isClosed ? const Color(0xFF475569) : const Color(0xFF15803D),
                        fontWeight: FontWeight.w800,
                        fontSize: 14,
                        letterSpacing: 0.5,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      isClosed
                          ? 'This incident has been marked as resolved'
                          : 'Direct to Lakhimpur Disaster Control Room',
                      style: const TextStyle(color: Color(0xFF64748B), fontSize: 12),
                    ),
                  ],
                ),
              ),
            ],
          ),

          const SizedBox(height: 16),
          const Divider(height: 1),
          const SizedBox(height: 14),

          // Report reference ID & timestamp
          Wrap(
            spacing: 12,
            runSpacing: 8,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Report Reference', style: TextStyle(fontSize: 11, color: Color(0xFF94A3B8))),
                  const SizedBox(height: 2),
                  SelectableText(
                    widget.service.serverReportId ?? widget.service.sosId ?? '',
                    style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 13, fontFamily: 'monospace'),
                  ),
                ],
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: isClosed ? const Color(0xFFE2E8F0) : const Color(0xFFDBEAFE),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  isClosed ? 'Closed' : 'Active · Received',
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w600,
                    color: isClosed ? const Color(0xFF475569) : const Color(0xFF1D4ED8),
                  ),
                ),
              ),
            ],
          ),

          const SizedBox(height: 16),

          // Gemini AI Triage Callout Box
          if (triage != null) ...[
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: isCritical ? const Color(0xFFFEF2F2) : const Color(0xFFF8FAFC),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: isCritical ? const Color(0xFFFCA5A5) : const Color(0xFFE2E8F0),
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Wrap(
                    spacing: 12,
                    runSpacing: 8,
                    children: [
                      Text(
                        '${triage['triage_source'] == 'gemini_ai' ? 'Gemini triage' : 'Report triage'} - $urgency',
                        style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w800, color: Color(0xFF0F172A)),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                        decoration: BoxDecoration(
                          color: isCritical ? const Color(0xFFDC2626) : const Color(0xFF3B82F6),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          score is num ? '$score/100' : 'Score unavailable',
                          style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.bold),
                        ),
                      ),
                    ],
                  ),
                  if (triage['summary'] != null) ...[
                    const SizedBox(height: 8),
                    Text(
                      triage['summary'].toString(),
                      style: const TextStyle(fontSize: 13, height: 1.4, color: Color(0xFF1E293B)),
                    ),
                  ],
                  if (triage['recommended_action'] != null) ...[
                    const SizedBox(height: 8),
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: const Color(0xFFCBD5E1)),
                      ),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Icon(Icons.info_outline, size: 16, color: Color(0xFF0284C7)),
                          const SizedBox(width: 6),
                          Expanded(
                            child: Text(
                              'Action: ${triage['recommended_action']}',
                              style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500, color: Color(0xFF0369A1)),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ],
              ),
            ),
            const SizedBox(height: 16),
          ],

          // Action Buttons
          if (!isClosed) ...[
            SizedBox(
              width: double.infinity,
              height: 44,
              child: OutlinedButton.icon(
                style: OutlinedButton.styleFrom(
                  foregroundColor: const Color(0xFF059669),
                  side: const BorderSide(color: Color(0xFF10B981), width: 1.5),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                ),
                onPressed: _closing ? null : _handleCloseRequest,
                icon: _closing
                    ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                    : const Icon(Icons.check_circle_outline, size: 18),
                label: Text(
                  _closing ? 'Closing Request…' : '✓ Close Request (Mark Resolved)',
                  style: const TextStyle(fontWeight: FontWeight.w700),
                ),
              ),
            ),
            const SizedBox(height: 10),
          ],

          SizedBox(
            width: double.infinity,
            height: 44,
            child: FilledButton.tonalIcon(
              style: FilledButton.styleFrom(
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
              ),
              onPressed: widget.onReset,
              icon: const Icon(Icons.add, size: 18),
              label: const Text('Send Another Report', style: TextStyle(fontWeight: FontWeight.w600)),
            ),
          ),
        ],
      ),
    );
  }

  // ==========================================
  // 2. TRANSMISSION FAILURE VIEW
  // ==========================================
  Widget _buildFailureCard(BuildContext context) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFFFEF2F2),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFF87171)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: const [
              Icon(Icons.warning_amber_rounded, color: Color(0xFFDC2626), size: 28),
              SizedBox(width: 10),
              Text(
                'Transmission Failed',
                style: TextStyle(color: Color(0xFFDC2626), fontWeight: FontWeight.bold, fontSize: 16),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            widget.service.errorMessage ?? 'Could not reach server.',
            style: const TextStyle(color: Color(0xFF7F1D1D), fontSize: 13, height: 1.4),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: FilledButton.icon(
                  onPressed: widget.service.isTransmitting ? null : widget.onRetry,
                  icon: const Icon(Icons.refresh, size: 16),
                  label: const Text('Retry Now'),
                ),
              ),
              const SizedBox(width: 10),
              OutlinedButton(
                onPressed: widget.onReset,
                child: const Text('Edit Report'),
              ),
            ],
          ),
        ],
      ),
    );
  }

  // ==========================================
  // 3. OFFLINE MESH VIEW (ESP32 LoRa ONLY)
  // ==========================================
  Widget _buildOfflineMeshCard(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final done = widget.service.stage == SOSStage.completed;

    return SOSStatusCard(
      locationReady: false,
      transmissionReady: false,
      requestContent: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(
              color: const Color(0xFFFEF3C7),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: const Color(0xFFF59E0B)),
            ),
            child: const Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.wifi_off, size: 14, color: Color(0xFFB45309)),
                SizedBox(width: 6),
                Flexible(child: Text(
                  'OFFLINE MESH MODE · ESP32 Node Required',
                  style: TextStyle(color: Color(0xFFB45309), fontSize: 11, fontWeight: FontWeight.bold),
                )),
              ],
            ),
          ),
          const SizedBox(height: 12),
          SelectableText(
            widget.service.sosId ?? '',
            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 8),
          Text(
            'Created: ${widget.service.createdAt == null ? '' : MaterialLocalizations.of(context).formatMediumDate(widget.service.createdAt!.toLocal())} '
            '${widget.service.createdAt == null ? '' : TimeOfDay.fromDateTime(widget.service.createdAt!.toLocal()).format(context)}',
            style: TextStyle(color: Colors.grey[600], fontSize: 12),
          ),
          const Divider(height: 28),
          _step(l10n.emergencyDataPrepared, 'SOS created on your device', true),
          _step(
            l10n.sendingToDevice,
            widget.service.stage == SOSStage.failed
                ? 'Transmission not confirmed'
                : 'Sending emergency information through AeroLink node',
            widget.service.aeroLinkConfirmed,
          ),
          _step(
            'Confirmed',
            'AeroLink node acknowledged your SOS',
            widget.service.aeroLinkConfirmed,
          ),
          _step(
            'Acknowledged',
            widget.service.baseStationAcknowledged
                ? 'Base station acknowledged your report'
                : 'Waiting for acknowledgement',
            widget.service.baseStationAcknowledged,
          ),
          _step(
            'Request completed',
            done
                ? 'You confirmed the problem is solved'
                : widget.service.completionId != null
                    ? 'Authorities requested closure. Your confirmation is needed.'
                    : 'Requires a request from authorities and your confirmation',
            done,
          ),
          if (widget.service.errorMessage != null) ...[
            const SizedBox(height: 12),
            Text(widget.service.errorMessage!, style: const TextStyle(color: Colors.deepOrange)),
          ],
          if (!widget.service.baseStationAcknowledged && !done && widget.service.completionId == null)
            TextButton.icon(
              onPressed: widget.service.isTransmitting ? null : widget.onRetry,
              icon: const Icon(Icons.refresh),
              label: Text(l10n.retryTransmission),
            ),
          if (widget.service.completionId != null)
            FilledButton(
              onPressed: widget.onReviewCompletion,
              child: const Text('Review completion request'),
            ),
          const Divider(height: 24),
          SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(
              onPressed: widget.onChat,
              icon: const Icon(Icons.chat_bubble_outline),
              label: Text(done ? 'View conversation' : 'Open chat'),
            ),
          ),
          if (done)
            TextButton(onPressed: widget.onReset, child: Text(l10n.sendAnotherSos)),
        ],
      ),
    );
  }

  Widget _step(String title, String subtitle, bool complete) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 18),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(
            complete ? Icons.check_circle : Icons.radio_button_unchecked,
            color: complete ? Colors.green : Colors.grey,
            size: 24,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(fontWeight: FontWeight.w600)),
                const SizedBox(height: 3),
                Text(subtitle, style: TextStyle(fontSize: 12, height: 1.4, color: Colors.grey[600])),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

