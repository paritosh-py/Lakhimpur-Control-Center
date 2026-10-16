import 'package:flutter/material.dart';

import '../../../services/sos_service.dart';

/// Placed above the navigator so a closure request can be reviewed on any page.
class SOSCompletionListener extends StatefulWidget {
  const SOSCompletionListener({
    super.key,
    required this.child,
    required this.navigatorKey,
  });
  final Widget child;
  final GlobalKey<NavigatorState> navigatorKey;
  @override
  State<SOSCompletionListener> createState() => _SOSCompletionListenerState();
}

class _SOSCompletionListenerState extends State<SOSCompletionListener> {
  String? _shownId;
  @override
  void initState() {
    super.initState();
    SOSService.instance.addListener(_changed);
    _changed();
  }

  void _changed() {
    final id = SOSService.instance.completionId;
    if (id == null || id == _shownId) return;
    _shownId = id;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final context = widget.navigatorKey.currentContext;
      if (mounted && context != null) {
        showSOSCompletionDialog(context, SOSService.instance);
      }
    });
  }

  @override
  void dispose() {
    SOSService.instance.removeListener(_changed);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => widget.child;
}

bool _completionDialogOpen = false;

Future<void> showSOSCompletionDialog(
  BuildContext context,
  SOSService service,
) async {
  if (_completionDialogOpen || service.completionId == null) return;
  _completionDialogOpen = true;
  bool busy = false;
  String? error;
  try {
    await showDialog<void>(
      context: context,
      barrierDismissible: false,
      builder: (dialogContext) => StatefulBuilder(
        builder: (context, setState) {
          Future<void> respond(bool resolved) async {
            setState(() {
              busy = true;
              error = null;
            });
            try {
              await service.respondToCompletion(resolved);
              if (dialogContext.mounted) Navigator.pop(dialogContext);
            } catch (e) {
              if (context.mounted) {
                setState(() {
                  busy = false;
                  error = e.toString().replaceFirst('Exception: ', '');
                });
              }
            }
          }

          return PopScope(
            canPop: !busy,
            child: AlertDialog(
              title: const Text('Is your problem solved?'),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Authorities have asked to complete request ${service.sosId}. Do you still need help?',
                  ),
                  if (busy)
                    const Padding(
                      padding: EdgeInsets.only(top: 16),
                      child: LinearProgressIndicator(),
                    ),
                  if (error != null)
                    Padding(
                      padding: const EdgeInsets.only(top: 12),
                      child: Text(
                        error!,
                        style: const TextStyle(color: Colors.red),
                      ),
                    ),
                ],
              ),
              actions: [
                TextButton(
                  onPressed: busy ? null : () => Navigator.pop(dialogContext),
                  child: const Text('Review later'),
                ),
                TextButton(
                  onPressed: busy ? null : () => respond(false),
                  child: const Text('I still need help'),
                ),
                FilledButton(
                  onPressed: busy ? null : () => respond(true),
                  child: const Text('Yes, complete request'),
                ),
              ],
            ),
          );
        },
      ),
    );
  } finally {
    _completionDialogOpen = false;
  }
}
