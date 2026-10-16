import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile/services/sos_service.dart';
import 'package:mobile/screens/sos/widgets/sos_transmission_stage_card.dart';

void main() {
  testWidgets('online sending never renders the mesh timeline; success requires a receipt', (tester) async {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final network = Completer<bool>();
    final receipt = Completer<Map<String, dynamic>>();
    final events = StreamController<Map<String, dynamic>>.broadcast(sync: true);
    var meshSends = 0;
    final service = SOSService(events: events.stream,
      sendPacket: (_) async { meshSends++; },
      checkOnline: () => network.future,
      sendOnline: (_) => receipt.future,
      closeOnline: (_) async => true);
    addTearDown(() async { service.dispose(); await events.close(); });
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: SingleChildScrollView(
      child: ListenableBuilder(listenable: service, builder: (_, _) => SOSTransmissionStageCard(
        service: service, onRetry: () {}, onReset: () {}, onChat: () {}, onReviewCompletion: () {},
      )),
    ))));
    final sending = service.sendSOS('{"incidentType":"rescue_sos"}');
    await tester.pump();
    expect(find.text('Checking connection'), findsOneWidget);
    network.complete(true);
    await tester.pump();
    expect(find.text('Sending directly to the dashboard'), findsOneWidget);
    expect(find.textContaining('AeroLink'), findsNothing);
    expect(service.isDeliveredOnline, false);
    events.add({'type':'ACK','sosId':service.sosId,'status':'BASE_STATION_RECEIVED'});
    expect(service.isDeliveredOnline, false);
    receipt.complete({'id':'REP-TEST','gemini_triage':{'urgency':'HIGH','urgency_score':80,'triage_source':'gemini_ai'}});
    await sending; await tester.pump();
    expect(find.text('DELIVERED VIA INTERNET'), findsOneWidget);
    expect(find.text('Active · Received'), findsOneWidget);
    expect(find.textContaining('AeroLink'), findsNothing);
    expect(meshSends, 0);
    expect(service.canChat, false);
    expect(await service.closeOnlineReport(), true);
    await tester.pump();
    expect(find.text('REPORT CLOSED / RESOLVED'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  test('online failure and retry do not invoke BLE; failed closure stays open with error', () async {
    final events = StreamController<Map<String, dynamic>>.broadcast();
    var attempt = 0;
    var meshSends = 0;
    final service = SOSService(events:events.stream,
      sendPacket: (_) async {meshSends++;}, checkOnline: () async => true,
      sendOnline: (_) async {if(attempt++ == 0) throw Exception('Server unavailable'); return {'id':'REP-TEST'};},
      closeOnline: (_) async => false);
    await service.sendSOS('{}');
    expect(service.stage,SOSStage.failed);
    expect(service.deliveryPath,SOSDeliveryPath.internet);
    expect(service.isTransmitting,false);
    await service.retry();
    expect(service.isDeliveredOnline,true);
    expect(await service.closeOnlineReport(),false);
    expect(service.stage,SOSStage.acknowledged);
    expect(service.errorMessage,contains('remains open'));
    expect(meshSends,0);
    service.dispose();await events.close();
  });

  test('connection-check failure exits sending state; missing report reference is not success', () async {
    final events = StreamController<Map<String, dynamic>>.broadcast();
    var failCheck = true;
    final service = SOSService(events:events.stream,sendPacket:(_) async => fail('No BLE expected'),
      checkOnline:() async {if(failCheck) throw Exception('plugin failure');return true;},
      sendOnline:(_) async => {});
    await service.sendSOS('{}');
    expect(service.isTransmitting,false);
    expect(service.errorMessage,contains('check the network'));
    failCheck=false;
    await service.retry();
    expect(service.stage,SOSStage.failed);
    expect(service.isDeliveredOnline,false);
    expect(service.errorMessage,contains('report reference'));
    service.dispose();await events.close();
  });

  testWidgets('closing report on dashboard automatically updates app to completed state', (tester) async {
    final events = StreamController<Map<String, dynamic>>.broadcast();
    var reportStatus = 'new';
    final service = SOSService(
      events: events.stream,
      sendPacket: (_) async {},
      checkOnline: () async => true,
      sendOnline: (_) async => {'id': 'REP-DASH-123', 'gemini_triage': {'urgency': 'HIGH'}},
      fetchReportStatus: (id) async => {'id': id, 'status': reportStatus},
    );
    addTearDown(() async { service.dispose(); await events.close(); });

    await tester.pumpWidget(MaterialApp(home: Scaffold(body: SingleChildScrollView(
      child: ListenableBuilder(listenable: service, builder: (_, _) => SOSTransmissionStageCard(
        service: service, onRetry: () {}, onReset: () {}, onChat: () {}, onReviewCompletion: () {},
      )),
    ))));

    await service.sendSOS('{}');
    await tester.pump();
    expect(find.text('Active · Received'), findsOneWidget);
    expect(service.stage, SOSStage.acknowledged);

    // Operator closes request on dashboard
    reportStatus = 'closed';
    // Advance timer by 3 seconds for status polling
    await tester.pump(const Duration(seconds: 4));

    expect(service.stage, SOSStage.completed);
    expect(find.text('REPORT CLOSED / RESOLVED'), findsOneWidget);
    expect(find.text('Closed'), findsOneWidget);
  });
}

