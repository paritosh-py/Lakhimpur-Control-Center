# AeroLink mobile project index

## Project map

Flutter mobile app, package name mobile. Entry point: lib/main.dart.
The app uses singleton ChangeNotifier services and StatefulWidget screens;
there is no provider/router framework. Navigation uses MaterialPageRoute.
Existing languages are English, Hindi and Marathi through generated Flutter
localizations and ARB files. New SOS/chat copy currently uses English.

| Area | Files / responsibility |
| --- | --- |
| App startup | lib/main.dart, lib/screens/splash_screen.dart |
| Home | lib/screens/home/home_screen.dart; widgets for map, GPS, weather, communication readiness |
| SOS form and request view | lib/screens/sos/sos_screen.dart |
| Shared SOS card shell | lib/screens/sos/widgets/sos_status_card.dart |
| Request identity and transmission timeline | lib/screens/sos/widgets/sos_transmission_stage_card.dart |
| Victim-authority chat | lib/screens/sos/sos_chat_screen.dart |
| App-wide completion popup | lib/screens/sos/widgets/sos_completion_listener.dart; attached above MaterialApp in main.dart |
| Request lifecycle and chat state | lib/services/sos_service.dart; injectable stream/sender for tests |
| Bluetooth transport | lib/services/ble_service.dart; scan, connect, discover, subscribe, framed JSON writes |
| Location and internet | lib/services/location_service.dart, lib/services/communication_service.dart |
| Weather | lib/services/weather_service.dart |
| Device management | lib/screens/more/aerolink/; connection, device details and base station |
| User settings | lib/screens/more/profile/, preferences/, emergency/, support/, about/ |
| Emergency contacts | lib/screens/more/emergency/models/ and services/ |
| Localization | lib/l10n/*.arb; lib/services/locale_controller.dart |
| Shared UI | lib/widgets/ |
| Platform shells | android/, ios/, linux/, macos/, windows/, web/ |
| Hardware | firmware/personal_node/, firmware/base_station/ |
| Tests | test/sos_service_test.dart, test/widget_test.dart |
| Wire protocol and hardware checks | docs/sos-protocol.md |

## SOS data path

SOS form -> SOSService (random ID, immutable creation time, payload) ->
BleService (newline-delimited UTF-8 JSON over BLE) -> personal ESP32 ->
Wi-Fi UDP port 4330 -> base station.

Base station -> unicast UDP port 4331 -> personal ESP32 -> BLE notifications ->
BleService.messages -> SOSService -> status card, chat and completion popup.

AeroLink receipt confirms only the personal-node stage. BASE_STATION_RECEIVED
acknowledges the base station. Chat ACKs do not advance the SOS timeline.
Closure requires COMPLETION_REQUEST, a victim decision, and acknowledgement of
that decision by the base station.

## State and scope

The SOS service retains the active request and conversation across navigation
within the running process. It does not persist across app termination.
The implementation currently has no internet SOS fallback, push service,
authority web dashboard, authentication, or background BLE delivery guarantee.
The included authority interface is the base station's Serial Monitor.
See the protocol document before flashing: the original sketches use a
different BLE framing format and must be upgraded together.

## Working-tree note

There were existing uncommitted localization and UI edits when this work began.
The SOS feature builds on that working tree; unrelated changes were not reset.

## File inventory
- firmware/base_station/base_station.ino
- firmware/personal_node/personal_node.ino
- lib/l10n/app_en.arb
- lib/l10n/app_hi.arb
- lib/l10n/app_localizations.dart
- lib/l10n/app_localizations_en.dart
- lib/l10n/app_localizations_hi.dart
- lib/l10n/app_localizations_mr.dart
- lib/l10n/app_mr.arb
- lib/main.dart
- lib/screens/home/home_screen.dart
- lib/screens/home/widgets/communication_readiness.dart
- lib/screens/home/widgets/header.dart
- lib/screens/home/widgets/map_module.dart
- lib/screens/home/widgets/weather_alerts.dart
- lib/screens/home/widgets/weather_alerts_screen.dart
- lib/screens/more/about/about_aerolink_screen.dart
- lib/screens/more/about/privacy_terms_screen.dart
- lib/screens/more/about/project_information_screen.dart
- lib/screens/more/aerolink/aerolink_device_screen.dart
- lib/screens/more/aerolink/base_station_screen.dart
- lib/screens/more/aerolink/widgets/base_station_location_card.dart
- lib/screens/more/aerolink/widgets/base_station_map.dart
- lib/screens/more/aerolink/widgets/base_station_status_card.dart
- lib/screens/more/aerolink/widgets/device_capabilities_card.dart
- lib/screens/more/aerolink/widgets/device_information_card.dart
- lib/screens/more/aerolink/widgets/device_status_card.dart
- lib/screens/more/emergency/emergency_contacts_screen.dart
- lib/screens/more/emergency/emergency_preferences_screen.dart
- lib/screens/more/emergency/models/emergency_contact.dart
- lib/screens/more/emergency/services/emergency_contact_service.dart
- lib/screens/more/emergency/widgets/add_contact_sheet.dart
- lib/screens/more/emergency/widgets/emergency_service_card.dart
- lib/screens/more/emergency/widgets/emergency_service_row.dart
- lib/screens/more/emergency/widgets/personal_contact_row.dart
- lib/screens/more/emergency/widgets/personal_contacts_card.dart
- lib/screens/more/emergency/widgets/preference_row.dart
- lib/screens/more/emergency/widgets/preference_section.dart
- lib/screens/more/more_screen.dart
- lib/screens/more/preferences/appearance_screen.dart
- lib/screens/more/preferences/notifications_screen.dart
- lib/screens/more/preferences/widgets/appearance_option_card.dart
- lib/screens/more/preferences/widgets/notification_section.dart
- lib/screens/more/preferences/widgets/notification_toggle.dart
- lib/screens/more/profile/personal_information_screen.dart
- lib/screens/more/support/contact_support_screen.dart
- lib/screens/more/support/help_center_screen.dart
- lib/screens/more/support/help_support_screen.dart
- lib/screens/more/support/report_issue_screen.dart
- lib/screens/more/widgets/more_menu_item.dart
- lib/screens/more/widgets/more_section.dart
- lib/screens/sos/sos_chat_screen.dart
- lib/screens/sos/sos_screen.dart
- lib/screens/sos/widgets/additional_details.dart
- lib/screens/sos/widgets/emergency_conditions.dart
- lib/screens/sos/widgets/people_affected_selector.dart
- lib/screens/sos/widgets/sos_action_button.dart
- lib/screens/sos/widgets/sos_completion_listener.dart
- lib/screens/sos/widgets/sos_information_card.dart
- lib/screens/sos/widgets/sos_status_card.dart
- lib/screens/sos/widgets/sos_transmission_stage_card.dart
- lib/screens/splash_screen.dart
- lib/services/ble_service.dart
- lib/services/communication_service.dart
- lib/services/locale_controller.dart
- lib/services/location_service.dart
- lib/services/sos_service.dart
- lib/services/weather_service.dart
- lib/widgets/app_bottom_navigation.dart
- lib/widgets/slide_fade_in.dart
- test/sos_service_test.dart
- test/widget_test.dart
