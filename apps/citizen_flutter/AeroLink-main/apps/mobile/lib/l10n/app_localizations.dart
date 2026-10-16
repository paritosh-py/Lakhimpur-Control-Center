import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_en.dart';
import 'app_localizations_hi.dart';
import 'app_localizations_mr.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'l10n/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
    : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations? of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations);
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
        delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
      ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('en'),
    Locale('hi'),
    Locale('mr'),
  ];

  /// No description provided for @appName.
  ///
  /// In en, this message translates to:
  /// **'AeroLink'**
  String get appName;

  /// No description provided for @home.
  ///
  /// In en, this message translates to:
  /// **'Home'**
  String get home;

  /// No description provided for @sos.
  ///
  /// In en, this message translates to:
  /// **'SOS'**
  String get sos;

  /// No description provided for @more.
  ///
  /// In en, this message translates to:
  /// **'More'**
  String get more;

  /// No description provided for @latestAlert.
  ///
  /// In en, this message translates to:
  /// **'Latest Alert'**
  String get latestAlert;

  /// No description provided for @weatherAndAlerts.
  ///
  /// In en, this message translates to:
  /// **'Weather & Alerts'**
  String get weatherAndAlerts;

  /// No description provided for @emergencyReadiness.
  ///
  /// In en, this message translates to:
  /// **'Emergency Readiness'**
  String get emergencyReadiness;

  /// No description provided for @emergencySOS.
  ///
  /// In en, this message translates to:
  /// **'Emergency SOS'**
  String get emergencySOS;

  /// No description provided for @liveLocation.
  ///
  /// In en, this message translates to:
  /// **'Live Location'**
  String get liveLocation;

  /// No description provided for @currentLocation.
  ///
  /// In en, this message translates to:
  /// **'Current Location'**
  String get currentLocation;

  /// No description provided for @refresh.
  ///
  /// In en, this message translates to:
  /// **'Refresh'**
  String get refresh;

  /// No description provided for @acquiring.
  ///
  /// In en, this message translates to:
  /// **'Acquiring...'**
  String get acquiring;

  /// No description provided for @acquiringGpsLocation.
  ///
  /// In en, this message translates to:
  /// **'Acquiring GPS location...'**
  String get acquiringGpsLocation;

  /// No description provided for @updatedJustNow.
  ///
  /// In en, this message translates to:
  /// **'Updated just now'**
  String get updatedJustNow;

  /// No description provided for @locationUnavailable.
  ///
  /// In en, this message translates to:
  /// **'Unavailable'**
  String get locationUnavailable;

  /// No description provided for @gps.
  ///
  /// In en, this message translates to:
  /// **'GPS'**
  String get gps;

  /// No description provided for @loadingWeather.
  ///
  /// In en, this message translates to:
  /// **'Loading weather...'**
  String get loadingWeather;

  /// No description provided for @weatherUnavailable.
  ///
  /// In en, this message translates to:
  /// **'Weather unavailable'**
  String get weatherUnavailable;

  /// No description provided for @internet.
  ///
  /// In en, this message translates to:
  /// **'Internet'**
  String get internet;

  /// No description provided for @aeroLinkDevice.
  ///
  /// In en, this message translates to:
  /// **'AeroLink Device'**
  String get aeroLinkDevice;

  /// No description provided for @connected.
  ///
  /// In en, this message translates to:
  /// **'Connected'**
  String get connected;

  /// No description provided for @unavailable.
  ///
  /// In en, this message translates to:
  /// **'Unavailable'**
  String get unavailable;

  /// No description provided for @searchingForDevice.
  ///
  /// In en, this message translates to:
  /// **'Searching for device'**
  String get searchingForDevice;

  /// No description provided for @notConnected.
  ///
  /// In en, this message translates to:
  /// **'Not connected'**
  String get notConnected;

  /// No description provided for @ready.
  ///
  /// In en, this message translates to:
  /// **'READY'**
  String get ready;

  /// No description provided for @offline.
  ///
  /// In en, this message translates to:
  /// **'OFFLINE'**
  String get offline;

  /// No description provided for @moreLabel.
  ///
  /// In en, this message translates to:
  /// **'More'**
  String get moreLabel;

  /// No description provided for @noActiveAlerts.
  ///
  /// In en, this message translates to:
  /// **'No Active Alerts'**
  String get noActiveAlerts;

  /// No description provided for @noEmergencyAlerts.
  ///
  /// In en, this message translates to:
  /// **'No emergency alerts are currently reported for your area.'**
  String get noEmergencyAlerts;

  /// No description provided for @deviceInformation.
  ///
  /// In en, this message translates to:
  /// **'Device Information'**
  String get deviceInformation;

  /// No description provided for @capabilities.
  ///
  /// In en, this message translates to:
  /// **'Capabilities'**
  String get capabilities;

  /// No description provided for @connectDevice.
  ///
  /// In en, this message translates to:
  /// **'Connect Device'**
  String get connectDevice;

  /// No description provided for @disconnectDevice.
  ///
  /// In en, this message translates to:
  /// **'Disconnect Device'**
  String get disconnectDevice;

  /// No description provided for @language.
  ///
  /// In en, this message translates to:
  /// **'Language'**
  String get language;

  /// No description provided for @helpAndSupport.
  ///
  /// In en, this message translates to:
  /// **'Help & Support'**
  String get helpAndSupport;

  /// No description provided for @aboutAeroLink.
  ///
  /// In en, this message translates to:
  /// **'About AeroLink'**
  String get aboutAeroLink;

  /// No description provided for @location.
  ///
  /// In en, this message translates to:
  /// **'Location'**
  String get location;

  /// No description provided for @locationAvailable.
  ///
  /// In en, this message translates to:
  /// **'Available'**
  String get locationAvailable;

  /// No description provided for @transmission.
  ///
  /// In en, this message translates to:
  /// **'Transmission'**
  String get transmission;

  /// No description provided for @transmissionReady.
  ///
  /// In en, this message translates to:
  /// **'Ready'**
  String get transmissionReady;

  /// No description provided for @transmissionNotReady.
  ///
  /// In en, this message translates to:
  /// **'Not Ready'**
  String get transmissionNotReady;

  /// No description provided for @emergencyTransmissionInfo.
  ///
  /// In en, this message translates to:
  /// **'Your latest location, name and contact details will be used for emergency transmission.'**
  String get emergencyTransmissionInfo;

  /// No description provided for @peopleAffected.
  ///
  /// In en, this message translates to:
  /// **'People Affected'**
  String get peopleAffected;

  /// No description provided for @emergencyConditions.
  ///
  /// In en, this message translates to:
  /// **'Emergency Conditions'**
  String get emergencyConditions;

  /// No description provided for @danger.
  ///
  /// In en, this message translates to:
  /// **'Danger'**
  String get danger;

  /// No description provided for @trapped.
  ///
  /// In en, this message translates to:
  /// **'Trapped'**
  String get trapped;

  /// No description provided for @evacuate.
  ///
  /// In en, this message translates to:
  /// **'Evacuate'**
  String get evacuate;

  /// No description provided for @medical.
  ///
  /// In en, this message translates to:
  /// **'Medical'**
  String get medical;

  /// No description provided for @additionalDetails.
  ///
  /// In en, this message translates to:
  /// **'Additional Details'**
  String get additionalDetails;

  /// No description provided for @describeEmergency.
  ///
  /// In en, this message translates to:
  /// **'Describe the emergency...'**
  String get describeEmergency;

  /// No description provided for @voice.
  ///
  /// In en, this message translates to:
  /// **'Voice'**
  String get voice;

  /// No description provided for @youCanTypeOrUseVoiceInput.
  ///
  /// In en, this message translates to:
  /// **'You can type or use voice input'**
  String get youCanTypeOrUseVoiceInput;

  /// No description provided for @holdToSendSos.
  ///
  /// In en, this message translates to:
  /// **'HOLD TO SEND SOS'**
  String get holdToSendSos;

  /// No description provided for @profile.
  ///
  /// In en, this message translates to:
  /// **'Profile'**
  String get profile;

  /// No description provided for @personalInformation.
  ///
  /// In en, this message translates to:
  /// **'Personal Information'**
  String get personalInformation;

  /// No description provided for @personalInformationSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Name, contact details and identity'**
  String get personalInformationSubtitle;

  /// No description provided for @emergency.
  ///
  /// In en, this message translates to:
  /// **'Emergency'**
  String get emergency;

  /// No description provided for @emergencyContacts.
  ///
  /// In en, this message translates to:
  /// **'Emergency Contacts'**
  String get emergencyContacts;

  /// No description provided for @emergencyContactsSubtitle.
  ///
  /// In en, this message translates to:
  /// **'People to notify during an emergency'**
  String get emergencyContactsSubtitle;

  /// No description provided for @emergencyPreferences.
  ///
  /// In en, this message translates to:
  /// **'Emergency Preferences'**
  String get emergencyPreferences;

  /// No description provided for @emergencyPreferencesSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Configure SOS behaviour'**
  String get emergencyPreferencesSubtitle;

  /// No description provided for @aeroLink.
  ///
  /// In en, this message translates to:
  /// **'AeroLink'**
  String get aeroLink;

  /// No description provided for @aeroLinkDeviceSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Connect and manage your device'**
  String get aeroLinkDeviceSubtitle;

  /// No description provided for @baseStation.
  ///
  /// In en, this message translates to:
  /// **'Base Station'**
  String get baseStation;

  /// No description provided for @baseStationSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Configure base station connection'**
  String get baseStationSubtitle;

  /// No description provided for @preferences.
  ///
  /// In en, this message translates to:
  /// **'Preferences'**
  String get preferences;

  /// No description provided for @notifications.
  ///
  /// In en, this message translates to:
  /// **'Notifications'**
  String get notifications;

  /// No description provided for @notificationsSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Alerts and emergency notifications'**
  String get notificationsSubtitle;

  /// No description provided for @appearance.
  ///
  /// In en, this message translates to:
  /// **'Appearance'**
  String get appearance;

  /// No description provided for @appearanceSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Theme and display preferences'**
  String get appearanceSubtitle;

  /// No description provided for @supportAndApp.
  ///
  /// In en, this message translates to:
  /// **'Support & App'**
  String get supportAndApp;

  /// No description provided for @helpAndSupportSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Get help using AeroLink'**
  String get helpAndSupportSubtitle;

  /// No description provided for @aboutAeroLinkSubtitle.
  ///
  /// In en, this message translates to:
  /// **'App information and version'**
  String get aboutAeroLinkSubtitle;

  /// No description provided for @tacticalMeshNetwork.
  ///
  /// In en, this message translates to:
  /// **'TACTICAL MESH NETWORK'**
  String get tacticalMeshNetwork;

  /// No description provided for @emergencyAlerts.
  ///
  /// In en, this message translates to:
  /// **'Emergency Alerts'**
  String get emergencyAlerts;

  /// No description provided for @alertsForCurrentLocation.
  ///
  /// In en, this message translates to:
  /// **'Alerts relevant to your current location'**
  String get alertsForCurrentLocation;

  /// No description provided for @alertMonitoringInfo.
  ///
  /// In en, this message translates to:
  /// **'Emergency alert monitoring will automatically update when new alerts are available.'**
  String get alertMonitoringInfo;

  /// No description provided for @liveGps.
  ///
  /// In en, this message translates to:
  /// **'LIVE GPS'**
  String get liveGps;

  /// No description provided for @locating.
  ///
  /// In en, this message translates to:
  /// **'LOCATING...'**
  String get locating;

  /// No description provided for @waitingForGps.
  ///
  /// In en, this message translates to:
  /// **'Waiting for GPS signal'**
  String get waitingForGps;

  /// No description provided for @sosDataUnavailable.
  ///
  /// In en, this message translates to:
  /// **'SOS data is unavailable. Please create a new SOS.'**
  String get sosDataUnavailable;

  /// No description provided for @voiceInputComingSoon.
  ///
  /// In en, this message translates to:
  /// **'Voice input will be available shortly.'**
  String get voiceInputComingSoon;

  /// No description provided for @checkingEmergencyReadiness.
  ///
  /// In en, this message translates to:
  /// **'Checking emergency readiness...'**
  String get checkingEmergencyReadiness;

  /// No description provided for @holdToActivateTransmission.
  ///
  /// In en, this message translates to:
  /// **'Hold to activate emergency transmission'**
  String get holdToActivateTransmission;

  /// No description provided for @emergencyDataPrepared.
  ///
  /// In en, this message translates to:
  /// **'Emergency data prepared'**
  String get emergencyDataPrepared;

  /// No description provided for @sendingToDevice.
  ///
  /// In en, this message translates to:
  /// **'Sending to AeroLink device'**
  String get sendingToDevice;

  /// No description provided for @waitingForDeviceConfirmation.
  ///
  /// In en, this message translates to:
  /// **'Waiting for device confirmation'**
  String get waitingForDeviceConfirmation;

  /// No description provided for @aeroLinkConfirmedSos.
  ///
  /// In en, this message translates to:
  /// **'AeroLink confirmed SOS'**
  String get aeroLinkConfirmedSos;

  /// No description provided for @sosTransmissionNotConfirmed.
  ///
  /// In en, this message translates to:
  /// **'The SOS transmission could not be confirmed.'**
  String get sosTransmissionNotConfirmed;

  /// No description provided for @retryTransmission.
  ///
  /// In en, this message translates to:
  /// **'Retry Transmission'**
  String get retryTransmission;

  /// No description provided for @emergencyInformationReceived.
  ///
  /// In en, this message translates to:
  /// **'Your emergency information has been received by the AeroLink device.'**
  String get emergencyInformationReceived;

  /// No description provided for @sendAnotherSos.
  ///
  /// In en, this message translates to:
  /// **'Send Another SOS'**
  String get sendAnotherSos;

  /// No description provided for @preparingEmergencySos.
  ///
  /// In en, this message translates to:
  /// **'Preparing Emergency SOS'**
  String get preparingEmergencySos;

  /// No description provided for @sendingEmergencySos.
  ///
  /// In en, this message translates to:
  /// **'Sending Emergency SOS'**
  String get sendingEmergencySos;

  /// No description provided for @waitingForConfirmation.
  ///
  /// In en, this message translates to:
  /// **'Waiting for Confirmation'**
  String get waitingForConfirmation;

  /// No description provided for @sosConfirmed.
  ///
  /// In en, this message translates to:
  /// **'SOS Confirmed'**
  String get sosConfirmed;

  /// No description provided for @transmissionFailed.
  ///
  /// In en, this message translates to:
  /// **'Transmission Failed'**
  String get transmissionFailed;

  /// No description provided for @preparingEmergencyInfo.
  ///
  /// In en, this message translates to:
  /// **'Preparing your emergency information for transmission.'**
  String get preparingEmergencyInfo;

  /// No description provided for @sendingEmergencyInfo.
  ///
  /// In en, this message translates to:
  /// **'Sending your emergency information to the AeroLink device.'**
  String get sendingEmergencyInfo;

  /// No description provided for @waitingForSosConfirmation.
  ///
  /// In en, this message translates to:
  /// **'Waiting for AeroLink to confirm that your SOS was received.'**
  String get waitingForSosConfirmation;

  /// No description provided for @deviceConfirmedReceipt.
  ///
  /// In en, this message translates to:
  /// **'The AeroLink device confirmed receipt of your emergency SOS.'**
  String get deviceConfirmedReceipt;

  /// No description provided for @deviceReceiptNotConfirmed.
  ///
  /// In en, this message translates to:
  /// **'We could not confirm that the AeroLink device received your SOS.'**
  String get deviceReceiptNotConfirmed;

  /// No description provided for @fullName.
  ///
  /// In en, this message translates to:
  /// **'Full Name'**
  String get fullName;

  /// No description provided for @phoneNumber.
  ///
  /// In en, this message translates to:
  /// **'Phone Number'**
  String get phoneNumber;

  /// No description provided for @emailAddress.
  ///
  /// In en, this message translates to:
  /// **'Email Address'**
  String get emailAddress;

  /// No description provided for @enterFullName.
  ///
  /// In en, this message translates to:
  /// **'Enter your full name'**
  String get enterFullName;

  /// No description provided for @enterPhoneNumber.
  ///
  /// In en, this message translates to:
  /// **'Enter your phone number'**
  String get enterPhoneNumber;

  /// No description provided for @enterEmailAddress.
  ///
  /// In en, this message translates to:
  /// **'Enter your email address'**
  String get enterEmailAddress;

  /// No description provided for @requiredNameAndPhone.
  ///
  /// In en, this message translates to:
  /// **'Please enter your name and phone number'**
  String get requiredNameAndPhone;

  /// No description provided for @personalInformationSaved.
  ///
  /// In en, this message translates to:
  /// **'Personal information saved'**
  String get personalInformationSaved;

  /// No description provided for @failedToSelectImage.
  ///
  /// In en, this message translates to:
  /// **'Failed to select image: {error}'**
  String failedToSelectImage(String error);

  /// No description provided for @personalInfoEmergencyUse.
  ///
  /// In en, this message translates to:
  /// **'This information can be included with your emergency transmission.'**
  String get personalInfoEmergencyUse;

  /// No description provided for @saveChanges.
  ///
  /// In en, this message translates to:
  /// **'Save Changes'**
  String get saveChanges;

  /// No description provided for @saveInformation.
  ///
  /// In en, this message translates to:
  /// **'Save Information'**
  String get saveInformation;

  /// No description provided for @editInformation.
  ///
  /// In en, this message translates to:
  /// **'Edit Information'**
  String get editInformation;

  /// No description provided for @emergencyContactsIntro.
  ///
  /// In en, this message translates to:
  /// **'Quickly access emergency services and manage people you want to contact during an emergency.'**
  String get emergencyContactsIntro;

  /// No description provided for @emergencyServices.
  ///
  /// In en, this message translates to:
  /// **'Emergency Services'**
  String get emergencyServices;

  /// No description provided for @personalEmergencyContacts.
  ///
  /// In en, this message translates to:
  /// **'Personal Emergency Contacts'**
  String get personalEmergencyContacts;

  /// No description provided for @done.
  ///
  /// In en, this message translates to:
  /// **'Done'**
  String get done;

  /// No description provided for @edit.
  ///
  /// In en, this message translates to:
  /// **'Edit'**
  String get edit;

  /// No description provided for @contactsNotificationInfo.
  ///
  /// In en, this message translates to:
  /// **'These contacts may be used for emergency notifications.'**
  String get contactsNotificationInfo;

  /// No description provided for @police.
  ///
  /// In en, this message translates to:
  /// **'Police'**
  String get police;

  /// No description provided for @emergencyAssistance.
  ///
  /// In en, this message translates to:
  /// **'Emergency assistance'**
  String get emergencyAssistance;

  /// No description provided for @ambulance.
  ///
  /// In en, this message translates to:
  /// **'Ambulance'**
  String get ambulance;

  /// No description provided for @medicalEmergency.
  ///
  /// In en, this message translates to:
  /// **'Medical emergency'**
  String get medicalEmergency;

  /// No description provided for @fireBrigade.
  ///
  /// In en, this message translates to:
  /// **'Fire Brigade'**
  String get fireBrigade;

  /// No description provided for @fireEmergency.
  ///
  /// In en, this message translates to:
  /// **'Fire emergency'**
  String get fireEmergency;

  /// No description provided for @requiredContactFields.
  ///
  /// In en, this message translates to:
  /// **'Please enter a name and phone number'**
  String get requiredContactFields;

  /// No description provided for @emergencyContact.
  ///
  /// In en, this message translates to:
  /// **'Emergency Contact'**
  String get emergencyContact;

  /// No description provided for @editEmergencyContact.
  ///
  /// In en, this message translates to:
  /// **'Edit Emergency Contact'**
  String get editEmergencyContact;

  /// No description provided for @addEmergencyContact.
  ///
  /// In en, this message translates to:
  /// **'Add Emergency Contact'**
  String get addEmergencyContact;

  /// No description provided for @updateEmergencyContact.
  ///
  /// In en, this message translates to:
  /// **'Update this emergency contact'**
  String get updateEmergencyContact;

  /// No description provided for @emergencyContactDescription.
  ///
  /// In en, this message translates to:
  /// **'Someone we can contact during an emergency'**
  String get emergencyContactDescription;

  /// No description provided for @relationship.
  ///
  /// In en, this message translates to:
  /// **'Relationship'**
  String get relationship;

  /// No description provided for @enterContactName.
  ///
  /// In en, this message translates to:
  /// **'Enter contact name'**
  String get enterContactName;

  /// No description provided for @relationshipHint.
  ///
  /// In en, this message translates to:
  /// **'Parent, friend, spouse...'**
  String get relationshipHint;

  /// No description provided for @saveContact.
  ///
  /// In en, this message translates to:
  /// **'Save Contact'**
  String get saveContact;

  /// No description provided for @addContactsBelow.
  ///
  /// In en, this message translates to:
  /// **'Add your emergency contacts below.'**
  String get addContactsBelow;

  /// No description provided for @noPersonalContacts.
  ///
  /// In en, this message translates to:
  /// **'No personal emergency contacts added.'**
  String get noPersonalContacts;

  /// No description provided for @addContact.
  ///
  /// In en, this message translates to:
  /// **'Add Contact'**
  String get addContact;

  /// No description provided for @emergencyPreferencesIntro.
  ///
  /// In en, this message translates to:
  /// **'Configure how AeroLink responds and shares information during an emergency.'**
  String get emergencyPreferencesIntro;

  /// No description provided for @emergencyActivation.
  ///
  /// In en, this message translates to:
  /// **'Emergency Activation'**
  String get emergencyActivation;

  /// No description provided for @holdToActivate.
  ///
  /// In en, this message translates to:
  /// **'Hold to Activate'**
  String get holdToActivate;

  /// No description provided for @preventsAccidentalSos.
  ///
  /// In en, this message translates to:
  /// **'Prevents accidental SOS activation'**
  String get preventsAccidentalSos;

  /// No description provided for @hold.
  ///
  /// In en, this message translates to:
  /// **'HOLD'**
  String get hold;

  /// No description provided for @shareLiveLocation.
  ///
  /// In en, this message translates to:
  /// **'Share Live Location'**
  String get shareLiveLocation;

  /// No description provided for @keepUpdatingLocation.
  ///
  /// In en, this message translates to:
  /// **'Keep updating your location during SOS'**
  String get keepUpdatingLocation;

  /// No description provided for @shareEmergencyContacts.
  ///
  /// In en, this message translates to:
  /// **'Share Emergency Contacts'**
  String get shareEmergencyContacts;

  /// No description provided for @shareContactsWithAuthorities.
  ///
  /// In en, this message translates to:
  /// **'Share your contact information with Basecamp Authorities'**
  String get shareContactsWithAuthorities;

  /// No description provided for @safety.
  ///
  /// In en, this message translates to:
  /// **'Safety'**
  String get safety;

  /// No description provided for @confirmationBeforeSos.
  ///
  /// In en, this message translates to:
  /// **'Confirmation Before SOS'**
  String get confirmationBeforeSos;

  /// No description provided for @askBeforeSos.
  ///
  /// In en, this message translates to:
  /// **'Ask before starting emergency transmission'**
  String get askBeforeSos;

  /// No description provided for @loudEmergencyAlert.
  ///
  /// In en, this message translates to:
  /// **'Loud Emergency Alert'**
  String get loudEmergencyAlert;

  /// No description provided for @playAlertWhenSosStarts.
  ///
  /// In en, this message translates to:
  /// **'Play an alert sound when SOS starts'**
  String get playAlertWhenSosStarts;

  /// No description provided for @noDeviceFound.
  ///
  /// In en, this message translates to:
  /// **'No AeroLink device found. Make sure the device is turned on and nearby.'**
  String get noDeviceFound;

  /// No description provided for @connectedToDevice.
  ///
  /// In en, this message translates to:
  /// **'Connected to {device}'**
  String connectedToDevice(String device);

  /// No description provided for @connectionFailed.
  ///
  /// In en, this message translates to:
  /// **'Connection failed: {error}'**
  String connectionFailed(String error);

  /// No description provided for @deviceDisconnected.
  ///
  /// In en, this message translates to:
  /// **'AeroLink device disconnected.'**
  String get deviceDisconnected;

  /// No description provided for @disconnectFailed.
  ///
  /// In en, this message translates to:
  /// **'Disconnect failed: {error}'**
  String disconnectFailed(String error);

  /// No description provided for @deviceScreenIntro.
  ///
  /// In en, this message translates to:
  /// **'Connect your AeroLink device to enable emergency communication when conventional networks are unavailable.'**
  String get deviceScreenIntro;

  /// No description provided for @searchingNearbyDevices.
  ///
  /// In en, this message translates to:
  /// **'Searching for nearby devices...'**
  String get searchingNearbyDevices;

  /// No description provided for @connectedAndReady.
  ///
  /// In en, this message translates to:
  /// **'Connected and ready'**
  String get connectedAndReady;

  /// No description provided for @noDeviceConnected.
  ///
  /// In en, this message translates to:
  /// **'No device connected'**
  String get noDeviceConnected;

  /// No description provided for @available.
  ///
  /// In en, this message translates to:
  /// **'Available'**
  String get available;

  /// No description provided for @deviceId.
  ///
  /// In en, this message translates to:
  /// **'Device ID'**
  String get deviceId;

  /// No description provided for @firmware.
  ///
  /// In en, this message translates to:
  /// **'Firmware'**
  String get firmware;

  /// No description provided for @battery.
  ///
  /// In en, this message translates to:
  /// **'Battery'**
  String get battery;

  /// No description provided for @emergencyTransmission.
  ///
  /// In en, this message translates to:
  /// **'Emergency Transmission'**
  String get emergencyTransmission;

  /// No description provided for @transmitSosThroughAeroLink.
  ///
  /// In en, this message translates to:
  /// **'Transmit SOS through AeroLink'**
  String get transmitSosThroughAeroLink;

  /// No description provided for @locationRelay.
  ///
  /// In en, this message translates to:
  /// **'Location Relay'**
  String get locationRelay;

  /// No description provided for @shareLocationDuringEmergencies.
  ///
  /// In en, this message translates to:
  /// **'Share location during emergencies'**
  String get shareLocationDuringEmergencies;

  /// No description provided for @offlineCommunication.
  ///
  /// In en, this message translates to:
  /// **'Offline Communication'**
  String get offlineCommunication;

  /// No description provided for @communicationWithoutInternet.
  ///
  /// In en, this message translates to:
  /// **'Communication without internet'**
  String get communicationWithoutInternet;

  /// No description provided for @baseStationIntro.
  ///
  /// In en, this message translates to:
  /// **'Nearby base stations can provide an additional communication path during an emergency.'**
  String get baseStationIntro;

  /// No description provided for @nearestBaseStation.
  ///
  /// In en, this message translates to:
  /// **'Nearest Base Station'**
  String get nearestBaseStation;

  /// No description provided for @aeroLinkBaseStation.
  ///
  /// In en, this message translates to:
  /// **'AeroLink Base Station'**
  String get aeroLinkBaseStation;

  /// No description provided for @searchingStationDetails.
  ///
  /// In en, this message translates to:
  /// **'Searching for station details'**
  String get searchingStationDetails;

  /// No description provided for @stationLocation.
  ///
  /// In en, this message translates to:
  /// **'Station Location'**
  String get stationLocation;

  /// No description provided for @nearestStation.
  ///
  /// In en, this message translates to:
  /// **'Nearest Station'**
  String get nearestStation;

  /// No description provided for @searchingForLocation.
  ///
  /// In en, this message translates to:
  /// **'Searching for location'**
  String get searchingForLocation;

  /// No description provided for @connectionStatus.
  ///
  /// In en, this message translates to:
  /// **'Connection Status'**
  String get connectionStatus;

  /// No description provided for @searchForBaseStations.
  ///
  /// In en, this message translates to:
  /// **'Search for Base Stations'**
  String get searchForBaseStations;

  /// No description provided for @baseStationStatus.
  ///
  /// In en, this message translates to:
  /// **'Base Station Status'**
  String get baseStationStatus;

  /// No description provided for @stationConnectedReady.
  ///
  /// In en, this message translates to:
  /// **'Connected and ready for transmission'**
  String get stationConnectedReady;

  /// No description provided for @stationDetectedNotConnected.
  ///
  /// In en, this message translates to:
  /// **'Station detected but not connected'**
  String get stationDetectedNotConnected;

  /// No description provided for @helpCenter.
  ///
  /// In en, this message translates to:
  /// **'Help Center'**
  String get helpCenter;

  /// No description provided for @contactSupport.
  ///
  /// In en, this message translates to:
  /// **'Contact Support'**
  String get contactSupport;

  /// No description provided for @reportAnIssue.
  ///
  /// In en, this message translates to:
  /// **'Report an Issue'**
  String get reportAnIssue;

  /// No description provided for @helpIntro.
  ///
  /// In en, this message translates to:
  /// **'Get help and find information about AeroLink.'**
  String get helpIntro;

  /// No description provided for @guidesAndFaq.
  ///
  /// In en, this message translates to:
  /// **'Guides and frequently asked questions'**
  String get guidesAndFaq;

  /// No description provided for @getAssistance.
  ///
  /// In en, this message translates to:
  /// **'Get assistance with AeroLink'**
  String get getAssistance;

  /// No description provided for @reportIssueSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Tell us about a problem you found'**
  String get reportIssueSubtitle;

  /// No description provided for @findAnswers.
  ///
  /// In en, this message translates to:
  /// **'Find answers and learn how to use AeroLink.'**
  String get findAnswers;

  /// No description provided for @howEmergencySosWorks.
  ///
  /// In en, this message translates to:
  /// **'How does Emergency SOS work?'**
  String get howEmergencySosWorks;

  /// No description provided for @howAddContacts.
  ///
  /// In en, this message translates to:
  /// **'How do I add emergency contacts?'**
  String get howAddContacts;

  /// No description provided for @howCommunicationWorks.
  ///
  /// In en, this message translates to:
  /// **'How does AeroLink communication work?'**
  String get howCommunicationWorks;

  /// No description provided for @howConnectDevice.
  ///
  /// In en, this message translates to:
  /// **'How can I connect an AeroLink device?'**
  String get howConnectDevice;

  /// No description provided for @detailedHelpComingSoon.
  ///
  /// In en, this message translates to:
  /// **'Detailed help information will be available here.'**
  String get detailedHelpComingSoon;

  /// No description provided for @contactSupportIntro.
  ///
  /// In en, this message translates to:
  /// **'Get in touch with the AeroLink support team.'**
  String get contactSupportIntro;

  /// No description provided for @emailSupport.
  ///
  /// In en, this message translates to:
  /// **'Email Support'**
  String get emailSupport;

  /// No description provided for @sendUsMessage.
  ///
  /// In en, this message translates to:
  /// **'Send us a message'**
  String get sendUsMessage;

  /// No description provided for @chatSupport.
  ///
  /// In en, this message translates to:
  /// **'Chat Support'**
  String get chatSupport;

  /// No description provided for @chatWithSupport.
  ///
  /// In en, this message translates to:
  /// **'Chat with our support team'**
  String get chatWithSupport;

  /// No description provided for @reportIssueIntro.
  ///
  /// In en, this message translates to:
  /// **'Tell us about any issue you experience with AeroLink.'**
  String get reportIssueIntro;

  /// No description provided for @describeIssue.
  ///
  /// In en, this message translates to:
  /// **'Describe the Issue'**
  String get describeIssue;

  /// No description provided for @describeWhatHappened.
  ///
  /// In en, this message translates to:
  /// **'Describe what happened...'**
  String get describeWhatHappened;

  /// No description provided for @submitReport.
  ///
  /// In en, this message translates to:
  /// **'Submit Report'**
  String get submitReport;

  /// No description provided for @theme.
  ///
  /// In en, this message translates to:
  /// **'Theme'**
  String get theme;

  /// No description provided for @appearanceIntro.
  ///
  /// In en, this message translates to:
  /// **'Choose how AeroLink looks on your device.'**
  String get appearanceIntro;

  /// No description provided for @light.
  ///
  /// In en, this message translates to:
  /// **'Light'**
  String get light;

  /// No description provided for @useBrightAppearance.
  ///
  /// In en, this message translates to:
  /// **'Use a bright appearance'**
  String get useBrightAppearance;

  /// No description provided for @dark.
  ///
  /// In en, this message translates to:
  /// **'Dark'**
  String get dark;

  /// No description provided for @reduceBrightness.
  ///
  /// In en, this message translates to:
  /// **'Reduce brightness in low-light environments'**
  String get reduceBrightness;

  /// No description provided for @systemDefault.
  ///
  /// In en, this message translates to:
  /// **'System Default'**
  String get systemDefault;

  /// No description provided for @matchDeviceAppearance.
  ///
  /// In en, this message translates to:
  /// **'Match your device appearance'**
  String get matchDeviceAppearance;

  /// No description provided for @display.
  ///
  /// In en, this message translates to:
  /// **'Display'**
  String get display;

  /// No description provided for @textSize.
  ///
  /// In en, this message translates to:
  /// **'Text Size'**
  String get textSize;

  /// No description provided for @adjustTextSize.
  ///
  /// In en, this message translates to:
  /// **'Adjust text size for better readability'**
  String get adjustTextSize;

  /// No description provided for @small.
  ///
  /// In en, this message translates to:
  /// **'Small'**
  String get small;

  /// No description provided for @defaultSize.
  ///
  /// In en, this message translates to:
  /// **'Default'**
  String get defaultSize;

  /// No description provided for @large.
  ///
  /// In en, this message translates to:
  /// **'Large'**
  String get large;

  /// No description provided for @extraLarge.
  ///
  /// In en, this message translates to:
  /// **'Extra Large'**
  String get extraLarge;

  /// No description provided for @textPreview.
  ///
  /// In en, this message translates to:
  /// **'This is how text will appear in AeroLink.'**
  String get textPreview;

  /// No description provided for @appLanguage.
  ///
  /// In en, this message translates to:
  /// **'App Language'**
  String get appLanguage;

  /// No description provided for @english.
  ///
  /// In en, this message translates to:
  /// **'English'**
  String get english;

  /// No description provided for @hindi.
  ///
  /// In en, this message translates to:
  /// **'Hindi'**
  String get hindi;

  /// No description provided for @marathi.
  ///
  /// In en, this message translates to:
  /// **'Marathi'**
  String get marathi;

  /// No description provided for @tamil.
  ///
  /// In en, this message translates to:
  /// **'Tamil'**
  String get tamil;

  /// No description provided for @telugu.
  ///
  /// In en, this message translates to:
  /// **'Telugu'**
  String get telugu;

  /// No description provided for @appearanceFooter.
  ///
  /// In en, this message translates to:
  /// **'Appearance settings affect the AeroLink interface on this device.'**
  String get appearanceFooter;

  /// No description provided for @notificationsIntro.
  ///
  /// In en, this message translates to:
  /// **'Control which alerts and updates AeroLink can send you.'**
  String get notificationsIntro;

  /// No description provided for @sosUpdates.
  ///
  /// In en, this message translates to:
  /// **'SOS Updates'**
  String get sosUpdates;

  /// No description provided for @sosUpdatesSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Updates about emergency transmissions'**
  String get sosUpdatesSubtitle;

  /// No description provided for @weatherAlerts.
  ///
  /// In en, this message translates to:
  /// **'Weather Alerts'**
  String get weatherAlerts;

  /// No description provided for @weatherAlertsSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Severe weather and environmental warnings'**
  String get weatherAlertsSubtitle;

  /// No description provided for @nearbyAlerts.
  ///
  /// In en, this message translates to:
  /// **'Nearby Alerts'**
  String get nearbyAlerts;

  /// No description provided for @nearbyAlertsSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Important emergencies near your area'**
  String get nearbyAlertsSubtitle;

  /// No description provided for @communication.
  ///
  /// In en, this message translates to:
  /// **'Communication'**
  String get communication;

  /// No description provided for @connectionChanges.
  ///
  /// In en, this message translates to:
  /// **'Connection Changes'**
  String get connectionChanges;

  /// No description provided for @connectionChangesSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Internet and communication availability'**
  String get connectionChangesSubtitle;

  /// No description provided for @deviceUpdatesSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Device connection and battery updates'**
  String get deviceUpdatesSubtitle;

  /// No description provided for @stationUpdatesSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Nearby station and connection updates'**
  String get stationUpdatesSubtitle;

  /// No description provided for @alertPreferences.
  ///
  /// In en, this message translates to:
  /// **'Alert Preferences'**
  String get alertPreferences;

  /// No description provided for @sound.
  ///
  /// In en, this message translates to:
  /// **'Sound'**
  String get sound;

  /// No description provided for @soundSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Play sound for important notifications'**
  String get soundSubtitle;

  /// No description provided for @vibration.
  ///
  /// In en, this message translates to:
  /// **'Vibration'**
  String get vibration;

  /// No description provided for @vibrationSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Vibrate for important notifications'**
  String get vibrationSubtitle;

  /// No description provided for @criticalAlertsInfo.
  ///
  /// In en, this message translates to:
  /// **'Emergency-critical alerts may still be shown even when some notification preferences are disabled.'**
  String get criticalAlertsInfo;

  /// No description provided for @emergencyCommunicationTagline.
  ///
  /// In en, this message translates to:
  /// **'Emergency communication when it matters most'**
  String get emergencyCommunicationTagline;

  /// No description provided for @appVersion.
  ///
  /// In en, this message translates to:
  /// **'App Version'**
  String get appVersion;

  /// No description provided for @versionNumber.
  ///
  /// In en, this message translates to:
  /// **'Version 1.0.0'**
  String get versionNumber;

  /// No description provided for @projectInformation.
  ///
  /// In en, this message translates to:
  /// **'Project Information'**
  String get projectInformation;

  /// No description provided for @projectInformationSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Learn about AeroLink and its mission'**
  String get projectInformationSubtitle;

  /// No description provided for @privacyAndTerms.
  ///
  /// In en, this message translates to:
  /// **'Privacy & Terms'**
  String get privacyAndTerms;

  /// No description provided for @privacyTermsSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Privacy policy and terms of use'**
  String get privacyTermsSubtitle;

  /// No description provided for @builtForReliability.
  ///
  /// In en, this message translates to:
  /// **'Built for reliable emergency communication'**
  String get builtForReliability;

  /// No description provided for @ourMission.
  ///
  /// In en, this message translates to:
  /// **'Our Mission'**
  String get ourMission;

  /// No description provided for @howAeroLinkWorks.
  ///
  /// In en, this message translates to:
  /// **'How AeroLink Works'**
  String get howAeroLinkWorks;

  /// No description provided for @emergencyFirst.
  ///
  /// In en, this message translates to:
  /// **'Emergency First'**
  String get emergencyFirst;

  /// No description provided for @aboutProjectBody.
  ///
  /// In en, this message translates to:
  /// **'AeroLink is designed to provide a reliable emergency communication system that can continue operating when conventional internet connectivity is unavailable.'**
  String get aboutProjectBody;

  /// No description provided for @missionBody.
  ///
  /// In en, this message translates to:
  /// **'Our goal is to improve emergency communication by helping people transmit critical information such as their identity, contact details and emergency information when they need help.'**
  String get missionBody;

  /// No description provided for @howItWorksBody.
  ///
  /// In en, this message translates to:
  /// **'The AeroLink ecosystem combines the mobile application, communication devices and base stations to help transmit emergency information through alternative communication layers.'**
  String get howItWorksBody;

  /// No description provided for @emergencyFirstBody.
  ///
  /// In en, this message translates to:
  /// **'AeroLink is designed around one principle: important emergency information should remain accessible and transmissible even when normal communication infrastructure becomes unreliable.'**
  String get emergencyFirstBody;

  /// No description provided for @privacy.
  ///
  /// In en, this message translates to:
  /// **'Privacy'**
  String get privacy;

  /// No description provided for @privacyBody.
  ///
  /// In en, this message translates to:
  /// **'AeroLink uses the information you provide to support emergency communication features. Personal and emergency information should be handled securely and only used when required for the intended functionality.'**
  String get privacyBody;

  /// No description provided for @termsOfUse.
  ///
  /// In en, this message translates to:
  /// **'Terms of Use'**
  String get termsOfUse;

  /// No description provided for @termsBody.
  ///
  /// In en, this message translates to:
  /// **'AeroLink is an emergency communication assistance system. It should not be considered a guaranteed replacement for official emergency services or communication infrastructure.'**
  String get termsBody;

  /// No description provided for @dataAndSecurity.
  ///
  /// In en, this message translates to:
  /// **'Data & Security'**
  String get dataAndSecurity;

  /// No description provided for @dataSecurityBody.
  ///
  /// In en, this message translates to:
  /// **'The application should use appropriate security mechanisms to protect stored and transmitted information. Security features and policies may evolve as the AeroLink system develops.'**
  String get dataSecurityBody;

  /// No description provided for @lastUpdated.
  ///
  /// In en, this message translates to:
  /// **'Last updated: September 2026'**
  String get lastUpdated;
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['en', 'hi', 'mr'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'en':
      return AppLocalizationsEn();
    case 'hi':
      return AppLocalizationsHi();
    case 'mr':
      return AppLocalizationsMr();
  }

  throw FlutterError(
    'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.',
  );
}
