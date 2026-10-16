import 'package:flutter/material.dart';

import '../../services/ble_service.dart';
import '../../services/sos_service.dart';

class SOSChatScreen extends StatefulWidget {
  const SOSChatScreen({super.key, required this.service});
  final SOSService service;
  @override
  State<SOSChatScreen> createState() => _SOSChatScreenState();
}

class _SOSChatScreenState extends State<SOSChatScreen> {
  final _controller = TextEditingController();
  bool _sending = false;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _send([SOSChatMessage? retry]) async {
    final text = retry?.text ?? _controller.text.trim();
    if (text.isEmpty || _sending) return;
    setState(() => _sending = true);
    // The transcript retains failed sends with a retry action.
    if (retry == null) _controller.clear();
    try {
      await widget.service.sendChat(text, retryMessage: retry);
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(error.toString().replaceFirst('Exception: ', '')),
          ),
        );
        if (retry == null &&
            !widget.service.messages.any((m) => m.text == text)) {
          _controller.text = text;
        }
      }
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: Listenable.merge([widget.service, BleService.instance]),
      builder: (context, _) {
        final service = widget.service;
        final connected = BleService.instance.isConnected;
        final enabled = connected && service.canChat && !_sending;
        return Scaffold(
          appBar: AppBar(title: const Text('Chat with authorities')),
          body: SafeArea(
            child: Column(
              children: [
                Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    children: [
                      Text(
                        service.sosId ?? '',
                        style: const TextStyle(fontWeight: FontWeight.w600),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        service.stage == SOSStage.completed
                            ? 'Request completed · Conversation history'
                            : !connected
                            ? 'AeroLink disconnected. Reconnect from the device screen.'
                            : !service.canChat
                            ? 'Waiting for AeroLink confirmation'
                            : 'Connected to AeroLink · Delivery requires a base-station reply',
                        textAlign: TextAlign.center,
                        style: const TextStyle(fontSize: 12),
                      ),
                    ],
                  ),
                ),
                Expanded(
                  child: service.messages.isEmpty
                      ? const Center(
                          child: Padding(
                            padding: EdgeInsets.all(24),
                            child: Text(
                              'Send an update to the authorities. Their replies will appear here.',
                              textAlign: TextAlign.center,
                            ),
                          ),
                        )
                      : ListView.builder(
                          reverse: true,
                          padding: const EdgeInsets.all(16),
                          itemCount: service.messages.length,
                          itemBuilder: (context, index) {
                            final message = service
                                .messages[service.messages.length - 1 - index];
                            return Align(
                              alignment: message.fromAuthority
                                  ? Alignment.centerLeft
                                  : Alignment.centerRight,
                              child: Container(
                                constraints: BoxConstraints(
                                  maxWidth:
                                      MediaQuery.sizeOf(context).width * .82,
                                ),
                                margin: const EdgeInsets.only(bottom: 12),
                                padding: const EdgeInsets.all(14),
                                decoration: BoxDecoration(
                                  color: message.fromAuthority
                                      ? Colors.white
                                      : const Color(0xFFFFE8DC),
                                  borderRadius: BorderRadius.circular(16),
                                ),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      message.fromAuthority
                                          ? 'Authorities'
                                          : 'You',
                                      style: const TextStyle(
                                        fontSize: 11,
                                        fontWeight: FontWeight.w700,
                                      ),
                                    ),
                                    const SizedBox(height: 5),
                                    SelectableText(message.text),
                                    const SizedBox(height: 6),
                                    Text(
                                      TimeOfDay.fromDateTime(
                                        message.createdAt.toLocal(),
                                      ).format(context),
                                      style: const TextStyle(fontSize: 10),
                                    ),
                                    if (!message.fromAuthority)
                                      Text(
                                        message.delivery ==
                                                MessageDelivery.delivered
                                            ? 'Received by base station'
                                            : message.delivery ==
                                                  MessageDelivery.sending
                                            ? 'Sending…'
                                            : 'Delivery unconfirmed',
                                        style: const TextStyle(fontSize: 11),
                                      ),
                                    if (message.delivery ==
                                            MessageDelivery.unconfirmed &&
                                        service.canChat)
                                      TextButton(
                                        onPressed: enabled
                                            ? () => _send(message)
                                            : null,
                                        child: const Text('Retry'),
                                      ),
                                  ],
                                ),
                              ),
                            );
                          },
                        ),
                ),
                if (service.stage != SOSStage.completed)
                  Padding(
                    padding: const EdgeInsets.all(12),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Expanded(
                          child: TextField(
                            controller: _controller,
                            enabled: enabled,
                            minLines: 1,
                            maxLines: 4,
                            maxLength: 600,
                            decoration: const InputDecoration(
                              hintText: 'Message authorities…',
                              border: OutlineInputBorder(),
                            ),
                          ),
                        ),
                        IconButton(
                          onPressed: enabled ? () => _send() : null,
                          tooltip: 'Send message',
                          icon: const Icon(Icons.send),
                        ),
                      ],
                    ),
                  ),
              ],
            ),
          ),
        );
      },
    );
  }
}
