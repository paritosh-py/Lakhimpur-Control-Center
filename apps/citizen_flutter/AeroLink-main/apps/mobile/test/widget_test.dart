import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/l10n/app_localizations.dart';
import 'package:mobile/services/sos_service.dart';
import 'package:mobile/screens/sos/widgets/sos_transmission_stage_card.dart';
import 'package:mobile/screens/sos/widgets/sos_completion_listener.dart';

void main() {
  testWidgets(
    'request card shows identity, stages and opens chat at narrow width',
    (tester) async {
      final events = StreamController<Map<String, dynamic>>.broadcast(
        sync: true,
      );
      final service = SOSService(
        events: events.stream,
        checkOnline: () async => false,
        sendPacket: (packet) async {
          events.add({
            'type': 'ACK',
            'status': 'BASE_STATION_RECEIVED',
            'sosId': packet['sosId'],
            'messageId': packet['messageId'],
          });
        },
      );
      addTearDown(() {
        service.dispose();
        events.close();
      });
      await service.sendSOS('{}');
      tester.view.physicalSize = const Size(360, 900);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      bool opened = false;
      await tester.pumpWidget(
        MaterialApp(
          localizationsDelegates: AppLocalizations.localizationsDelegates,
          supportedLocales: AppLocalizations.supportedLocales,
          home: Scaffold(
            body: SingleChildScrollView(
              child: SOSTransmissionStageCard(
                service: service,
                onRetry: () {},
                onReset: () {},
                onChat: () => opened = true,
                onReviewCompletion: () {},
              ),
            ),
          ),
        ),
      );
      expect(find.text(service.sosId!), findsOneWidget);
      expect(find.text('Confirmed'), findsOneWidget);
      expect(find.text('Acknowledged'), findsOneWidget);
      expect(find.text('Request completed'), findsOneWidget);
      await tester.ensureVisible(find.text('Open chat'));
      await tester.tap(find.text('Open chat'));
      expect(opened, isTrue);
      expect(tester.takeException(), isNull);
    },
  );

  testWidgets(
    'completion popup keeps request open when victim still needs help',
    (tester) async {
      final events = StreamController<Map<String, dynamic>>.broadcast(
        sync: true,
      );
      final service = SOSService(
        events: events.stream,
        checkOnline: () async => false,
        sendPacket: (packet) async {
          events.add({
            'type': 'ACK',
            'status': packet['type'] == 'SOS'
                ? 'BASE_STATION_RECEIVED'
                : 'COMPLETION_RESPONSE_RECEIVED',
            'sosId': packet['sosId'],
            'messageId': packet['messageId'],
          });
        },
      );
      addTearDown(() {
        service.dispose();
        events.close();
      });
      await service.sendSOS('{}');
      events.add({
        'type': 'COMPLETION_REQUEST',
        'sosId': service.sosId,
        'messageId': 'close',
      });
      await tester.pumpWidget(
        MaterialApp(
          home: Builder(
            builder: (context) => Scaffold(
              body: TextButton(
                onPressed: () => showSOSCompletionDialog(context, service),
                child: const Text('Review'),
              ),
            ),
          ),
        ),
      );
      await tester.tap(find.text('Review'));
      await tester.pumpAndSettle();
      expect(find.text('Is your problem solved?'), findsOneWidget);
      await tester.tap(find.text('I still need help'));
      await tester.pumpAndSettle();
      expect(service.stage, SOSStage.acknowledged);
      expect(find.text('Is your problem solved?'), findsNothing);
    },
  );
}
