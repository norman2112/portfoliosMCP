# Changelog
## 7.16.6
- Add ability to filter by scope [#1117]

## 7.16.5
- Add Dependency on tenant group id for connected apps instead of tenant id [#1122]

## 7.16.4
- Allow filtering by all custom attributes regardless of being enabled in list view or not [#1121]

## 7.16.3
- Allow only manage and edit roles to delete, insert and update an objective [#1075]

## 7.16.2
- Show upcoming target column by default in list view [#1096]

## 7.16.1
- Show objectives if KR matches filter[#1097]

## 7.16.0
- Add custom attribute values in Multi Level OKRs API [#1072]
- Add ability to filter by custom attribute values [#1093]

## 7.15.9
- Fixed the issue with objective card status not saved [#1091]

## 7.15.8
- Add async api helm chart and values [#1083]

## 7.15.7
- Rest Api v2 version fetch objectives api [#1059]

## 7.15.6
- MLQ to return empty list if wic not found, basic current user to return 400 if role is none for specific context [#1071]

## 7.15.5
- remove external api call logs [#1069]

## 7.15.4
- Current User Refactoring [#1050]
- Update Changelog for Current User Refactoring [#1051]

## 7.15.3
- Refactor Multi Level OKRs API [#1043]

## 7.15.2
- Add logs for pf new api version [#1045]

## 7.15.1
- Fix the migration failure due to hasura upgrade [#1036]

## 7.15.0
- Delete work item container API [#1019]
- Permissions fix for work item container API [#1037]
- Permissions for color config bug [#1038]

## 7.14.0
- Activity's OKRs API [#1025]

## 7.13.2
- Reduce pubnub calls to objective tree [#1034]

## 7.13.0
- Add Upcomming targets for multilevel query [#1010]
- Update constantane version to 3.3.0 [#1026]

## 7.12.0
- Update release version to 7.13.0 in changelog [#1027]

## 7.11.0
- Color threshold configuration[#995]

## 7.10.3
- Inline edit apis for objective and keyresult [#998]
- Udpate jinja version to 3.1.6 [#1017]
- Remove primary level restriction for level deletion [#1015]

## 7.10.2
- Added log for external API failure [#1018]

## 7.10.1
- Update aiohttp and werkzeug versions [1005]
- Added permissions for rolled_up_progress_percentage to OData Hasura[#1012]

## 7.9.2
- Error massage handling for deletion of level configs [1001]

## 7.9.1
- level config settings get log [1008]

## 7.8.2
- Get Level config changes with actions and permissions [#1000]

## 7.8.1
- Refactor OKRs APIs[#1002]

## 7.7.0
- Add fetch objective activity logs APIs[#989]
- Add fetch key results activity logs APIs[#989]
- Add fetch bulk key results APIs[#989]

## 7.6.0
- Added objective progress percentage rollup[#956]

## 7.5.0
- Add migration files for rollup[#985]

## 7.4.0
- Add OKRs APIs[#980]

## 7.3.3

- Revert New portfolip api version changes[#974]

## 7.3.2
- Fix key result custom attribute history when insert[#972]

## 7.3.1
- Fix multi level okr filter lists empty result bug [#970]
- Portfolio new api version support [#960]

## 7.3.0
- Add multi level okr filter lists [#968]

## 7.2.0
- Return 3 levels of objectives and key results in multi-level-okrs api [#965]
- Fix CD pipeline failure [#965]

## 7.1.2
- Fix CI pipeline failure and use constantine v3.1.2 [#966]

## 7.1.1
- Return 2 levels of objectives and key results in multi-level-okrs api [#962]

## 7.1.0
- Add filter by owner in multi level okr [#949]

## 7.0.6
- Handle Chunked Response [#952]

## 7.0.5
- log portfoli strategy api [#951]

## 7.0.4
- log external apis for portfolios [#950]

## 7.0.3
- update platforma_check_objective_level_depth_update_trigger for deleted_at_epoch [#932]

## 7.0.2
- Add multi level okr custom action[#933]

## 7.0.1

- Updating progress percentage of Objective and Key results for activity log entry after deletion of progress point entry.[#934]
- Removed container ids as input for list_activity_container actions [#930]
- Handle owners column in column configs[#942]

## 7.0.0

- constantine-v2 changes for ci/cd[#936]

## 6.3.19

- stop recursive pubnub events[#923]

## 6.3.18

- Added event triggers for datascience[#915]
- - update urllib3 package [#922]
- update setup tools library[#927]

## 6.3.17
- activity logs for Customize column configs [#919]
- Increased expiration limit of inactive WIC to 30 days[#918]
- add user settings mode for Customize colum configs [#908]

## 6.3.16
- Update Custom Attributes settings tooltip[#913]

## 6.3.15
- Update idna and zipp[#912]

## 6.3.14
- Fix objective's dates out of range changes bug[#911]

## 6.3.13
- User Settings Models[#906]

## 6.3.12
- Update idna[#901]
- Return key result name for targets and update custom attributes[#898]

## 6.3.11
- Remove unwanted hasura permissions[#902]

## 6.3.10
- Fix objective progress percentage in history[#897]

## 6.3.9
- update aiohttp, sentry libs and certifi[#896]

## 6.3.8
- Werkzeug upgrade[#893]
- update aiohttp and sentry libs[#896]

## 6.3.7
- Odata hasura migration for targets[#892]

## 6.3.6
- update key resutls date trigger[#889]
- avoid deleted projects[#890]

## 6.3.5
- Enable multi target hasura events[#887]

## 6.3.4
- Objective date bound in API[#888]

## 6.3.3
- Fix for target value error[#884]

## 6.3.2
- Update custom actions for multi targets [#881]

## 6.3.1
- Deletion of Objective or Keyresult cascades to targets [#864]

## 6.3.0
- Hasura Upgrade to 2.37.0 [#871]
- remove delete action for objectives model from hasura [#850]

## 6.2.3

- Add targets model and hasura permissions [#856]

## 6.2.2

- Fix deleted child objective change level bug [#854]
- Jinja upgrade to 3.1.4 [#854]
- Staging cluster change  [#851]

## 6.2.1

- Fix the key result tab failure on a new board [#849]

## 6.2.0

- OKRs Work Feature [#813]

## 6.1.25

- added only migrations for work feature exclusively [#826]

## 6.1.24

- Fix for detached instance error in current-user [#823]

## 6.1.23

- Perceived performance  [#818]

## 6.1.22

- Using single PubNub object and updated requests to 2.32.2 [#811]

## 6.1.21

- Remove delete wics call [#794]

## 6.1.20

- New feature Custom Attributes label [#788]

## 6.1.19

- add cleaning wics [#785]
- add more logs for planview user id and tenant group id [#783]

## 6.1.18

- Remove progress point event based progress calculation [#774]
- Add api response time log [#774]

## 6.1.17

- Fix for child - parent objective update failure bug [#764]

## 6.1.16

- Fix for child - parent objective update failure bug [#749]

## 6.1.15

- Stop printing env variables as it has conerns with security [#741]

## 6.1.14

- Exclude containers with null [#738]
- Pubnub - not sending to correct channel when tenant group id is NULL [#729]
- Stop registering integration hub [#728]
- Updating github runner role to new rolename [#723]
- Update in github role arn [#724]

## 6.1.13 - 2024-02-21

- Increase text limit for CA and recalculate progress percentage [#717]

## 6.1.12 - 2024-02-05

- pv admin validation for owned_by validation [#713]

## 6.1.11 - 2024-02-02

- Revert show latest label of custom attribute in history [#710]
- Add app_owned_by validation for all krs and objective actions [#709]
- Add new permisson to protect from non pv admin user creates data from [#708]
- Custom attributes values last updated by is not updated properly [#707]
- Incorrect json for boolean values in for custom attribute text field [#706]
- Show latest label of custom attribute in history [#705]

## 6.1.10 - 2024-01-02

- Fix Pubnub issue for progress points [#699]
- History API/action for Objectives and Key results [#669]

## 6.1.9 - 2023-12-12

- Fixes for the CI/CD pipelines (no code changes)

## 6.1.8 - 2023-12-07

- Switch to new CI/CD process developed by Constantine (no code changes)

## 6.1.7 - 2023-11-27

- Add Custom attribute tables in triggers to sync updated_at columns [#654]
- History shows wrong User name for updating objective and Key results [#651]
- Fix filter condition for connecting the right work item [#650]
- Mend issue fixed with urllib3 [#649]
- Use default value for levels in WIC if settings not found [#648]
- Select correct WIC from tenant information bug [#647]

## 6.1.6 - 2023-10-23

- Fix for the Key result starting value bug [#646]

## 6.1.5 - 2023-10-17

- Custom attributes values API [#594]
- Fix for nullable fields in the API [#645]

## 6.1.4 - 2023-10-09

### Added

- Code changes for the new Migration process [#593]

## 6.1.3 - 2023-09-21

### Fixed

- Priority workaround for Portfolio api max limit [#600]
- Mend issue fixes [#592]

### Added

- Custom Attribute Config APIs [#591]
- Migrations and tables for Custom Attributes [#588]

## 6.1.2 - 2023-07-20

### Fixed

- Add special case handling for activity log insert fails [#586]

### Added

- Add the key to send app_owned_by changes updates [#581]
- Add pubnub events for updates to description field [#584]

## 6.1.1 - 2023-06-30

### Fixed

- Fix migration importer bug for autogenerated fields [#585]

## 6.1.0 - 2023-06-21

### Added

- Update APIs for multiple product types [#563]
- Add generated fields for tenant id and columns [#544]
- Change hasura permissions for app_name fields [#553]
- Primary work for external API changes [#560]
- Various fixes for connected apis [#572]
- Changelog update [#582]
- Release 6.1.0 [#583]

### Fixed

- Fix for empty key results [#561]
- Fix for loading empty key results [#562]
- Fix multiple API bugs for connected scenarios [#568]
- Fix pubnub event for connected okrs [#569]
- Fix search_users and refactor input prepper [#571]
- Fix users_info to fetch and merge info from both apps [#573]
- Fix trigger validation for objectives [#574]
- Pubnub and list activities fixes [#575]
- Fix getting of tenant user id [#580]

## 6.0.4 - 2023-05-17

### Fixed

- Fix level config insert on work item container insert [#567]

## 6.0.3 - 2023-05-11

### Added

- Add a tool for tenant migration [#555]
- New roles and permissions for Hasura reporting [#557]

### Fixed

- Exclude activities for deleted AgilePlace cards [#564]
- Add missing message field in level config errors [#565]

## 6.0.2 - 2023-02-13

### Added

- Implementation of PubNub backend [#540]
- Upgrade version of dependencies according to security findings [#541]
- Infra: update composite action to consolidated form [#548]
- Add events for KeyResultsTab and KeyResultsCount components [#551]

### Fixed

- Vulnerability alert for sentry SDK [#546]
- Vulnerability alert for connexion SDK [#547]
- Fixed CHANGELOG [#549]
- PubNub Bug fixes [#550]

## 6.0.1 - 2022-11-30

### Added

- Use new API service from PVID for user map [#543]
- Release PR [#545]

### Fixed

- API changes listing objectives and activities [#538]
- Modify unique constraint to fix same day deletion and update bug [#539]
- Add missing env variable for Slack notifications [#542]

## 5.1.4 - 2022-11-08

### Fixed

- Do not delete child objectives when deleting parent [#537]

## 5.1.3 - 2022-10-28

### Fixed

- Remove the OR check as it is not necessary [#536]

## 5.1.2 - 2022-10-26

### Added

- Add .whitesource configuration file [#530]
- Update production deployment to adapt to migration [#534]

### Fixed

- Add check for not empty string in queries [#535]

## 5.1.1 - 2022-09-15

### Added

- Initial work for PRM api integration with OKR actions [#513]
- API changes for list activities and list activity containers [#511]
- API changes necessary for front end to work without integration hub [#518]
- Add required info in the output of list_activities action [#519]
- Add new action for users information and fix error message [#520]
- Schema and response changes for search_users and users_info actions [#521]
- Update metadata for users_info action [#522]
- Add unmapped users ids table [#524]
- Create README.rst [#525]
- Alter unmapped user ids table to store user ids as strings [#526]
- Update Hasura permissions to remove the costly OR condition [#529]
- Add .whitesource configuration file [#530]
- Update production deployment to adapt to migration [#534]

### Fixed

- Fix level config bugs w.r.t PV Admin settings [#523]
- Upgrade poetry version to 7 [#528]
- Add check for not empty string in queries [#535]
- Remove the OR check as it is not necessary [#536]

## 5.1.0 - 2022-08-10

### Added

- Call Planview ID API when Leankit does not return the Planview user  [#487]
- Preset app_name from PTS token and use that in all CRUD operations [#496]
- Use pts token format for all requests [#489]
- Add penetration testing and turn off development environment deployment [#499]
- Add penetration testing and turn off development [#501]
- Make last updated by consistent with other changes [#505]
- Prepare database and API for E1 integration [#506]
- Add services and actions for new Leankit APIs [#502]
- Ci improvement [#507]
- Add new audit table for PVID migration [#512]

### Fixed

- Fix permission preset - created_by instead of created_at [#495]
- Add new columns and Hasura permissions for PVID changes. [#478]
- infra(1759621891): Fix workflow to trigger on merge to main [#497]
- Update deployment to not require kubecontext and change target cluster [#503]
- Fix miscellaneous issues for pvid integration [#498]
- Change comparison to org and user id which has fallback option [#504]
- Fix how we access app specific user id [#508]
- Fix conditions in triggers to take into account selecting by tenant group id [#509]
- Update validations for org and user in JWT token [#510]
- Update tenant id and user id checks to not include empty strings [#515]
- Fix yaml indent issue for api testing step [#514]
- Fix or comment api tests failure post deploy [#516]
- Fix slack notification failure [#517]

## 5.0.11 - 2022-06-22

### Added

- Board access changes. [#492]

### Fixed

- Fix view migrations. [#494]
- Add new columns and Hasura permissions for PVID changes. [#478]

## 5.0.10 - 2022-06-01

### Fixed

- Fix bug in eradicator which leaves orphan records. [#493]

## 5.0.9 - 2022-06-01

### Fixed

- Add foreign key relation between WorkItemContainerRole and WorkItemContainer. [#491]

## 5.0.8 - 2022-06-01

### Fixed

- Add foreign key relationship between WorkItem and WorkItemContainer. [#490]

## 5.0.7 - 2022-05-20

### Fixed

- Create test deployment for staging environment. [#485]

## 5.0.6 - 2022-05-19

### Fixed

- Add new action for inserting a level. [#484]

## 5.0.5 - 2022-05-06

### Fixed

- Add ssl verification and do not use default one by aiohttp. [#486]

## 5.0.4 - 2022-04-27

### Fixed

- Remove check for config levels to be unique color. [#482]

## 5.0.3 - 2022-04-13

### Fixed

- Fix filter condition for level config deletion. [#481]

## 5.0.2 - 2022-02-15

### Added

- Change the input prepper. [#476]

### Fixed

- Fix filter condition for level config deletion. [#480]

## 5.0.1 - 2022-02-15

### Added

- SUMMARY added to the import logs. [#473]
- `delete-organization` endpoint. [#474]

### Fixed

- Exporter added to manifest adapter. [#465]
- Change unique index for WICs and WIs. [#468]
- Set bucket suffixes for production and dev. [#469]
- Adapted manifest now has SUMMARY. [#471]
- Work item card status corrected. [#475]

## [5.0.0] - 2022-01-25

### Changed

- Better serialization with `to_dict` by OpenAlchemy. [#441]

### Added

- Add a way to parse different JWT token types. [#440]
- Add importer module for migration of data to new installation. [#442]
- Add tenant migration logs table. [#443]
- Add tenant eradicator. [#444]
- PTS token used in leankit external api. [#445]
- PTS token generator task. [#448]
- Add the exporter for the adapted manifest. [#454]
- Add indexed to common date fields. [#459]
- Add the importer for leankit manifest. [#462]
- Add docker for local dev. [#463]

### Fixed

- Fixed the jwt decoding error for `aud` key. [#453]

## [4.7.0] - 2021-10-06

### Fixed

Fixed issue with views, introduced in #415. [#422]

### Changed

- Gunicorn now part of the application. [#411]
- Updated views to use `deleted_at_epoch`. [#415]
- Migration that reapplies all triggers and removes old triggers. [#431]

### Added

- Added readme and sample commands for anonymizing data. [#412]
- Added the ability to generate a migration of triggers. [#426]
- Select permissions for progress percentages. [#427]

## [4.6.7] - 2021-08-05

### Changed

- Indexed columns and added `adapter_kwargs`. [#408]

## [4.6.6] - 2021-08-05

### Fixed

- Fixed timestamp trigger for `WorkItemContainerRole`. [#405]
- Fixed bad query/loop in `current_user`. [#406]

## [4.6.5] - 2021-08-05

### Changed

- Updated docker-entrypoint to use gunicorn workers. [#402]
- Moved Sentry Trace Rate to settings. [#403]

### Added

- Soft-delete implemented on OKRs. [#386]

### Fixed

- Fixed Hasura update trigger to listen for `deleted_at_epoch`. [#401]

## [4.6.4] - 2021-08-03

### Fixed

- Single query of WIC roles for find/build phase of `current_user`. [#398]

### Changed

- Installed `pytest-dotenv` as dev dependency. [#399]

## [4.6.3] - 2021-07-30

### Fixed

- Timestamps in ORM now fetch from the database. [#395]

## [4.6.2] - 2021-07-29

### Changed

- Changed all uses of db_session to use a context manager. [#393]

## [4.6.1] - 2021-07-27

### Changed

- Changed db_session to use a context manager in `current_user`. [#391]

## [4.6.0] - 2021-07-22

### Added

- Add `deleted_at` to tables for soft delete. [#384]
- Add retry to IH subscriptions. [#385]

### Changed

- Change to decorator-style validations. [#381]
- Change the trigger function for wics to disallow certain columns. [#383]

### Fixed

- Fix the pattern matching for the external_ids in the api. [#382]
- Fix no privilege update in work item container roles. [#387]

## [4.5.2] - 2021-06-23

### Added

- Add the `okrs_consumer` role to Hasura. [#373]
- Add FactoryBoy to development for tests. [#375]
- Add triggers to validate dates for objectives and key results. [#377]

### Fixed

- Fixed broken trigger that makes sure `parent_objective_id` is valid. [#374]

### Changed

- Changed the environment variables for incoming hasura jwt secret. [#376]

## [4.5.1] - 2021-06-09

### Added

- Add re-leveling after a level deletion. [#366]
- Create triggers on objectives for `parent_objective_id`
  in relation to `work_item_container` access. [#369]

### Changed

- Change the timeframe columns in Objectives and KeyResults to be non-null. [#367]
- Change objective level_depth trigger. [#370]

### Fixed

- Change the `tenant_op` for IH registrations to `add`. [#371]

## [4.5.0] - 2021-06-02

### Added

- Add `action_type` to `update_level_config`. [#358]
- Add validations for level removal for `update_level_config`. [#359]
- Migration and add delete endpoint for deleting a level from the level config. [#360]

### Changed

- Set wic defaults for `default_level_depth` and `objective_editing_levels`. [#355]
- Change the errors format returned from validations. [#361]
- Remove `action_type` requirement for `update_level_config`. [#363]

### Fixed

- Fix issue involving missing WorkItemContainer for WorkItemContainerRole. [#364]

## [4.4.2] - 2021-05-23

### Added

- Add `tenant_id_str` filtering to the re-provisioning cron. [#354]

### Changed

- Changed orphaned WICs to be deleted by cron job. [#352]
- Migration: Add `WorkItemContainerRole` table and model. [#338]

### Fixed

- Timestamps may now be queried. [#351]

## [4.4.1] - 2021-05-18

- Add one-off job for re-registering customers and work items. [#347]

## [4.4.0] - 2021-05-18

### Added

- Add additional validation and requirements for domain. [#342]

### Changed

- Migration: Parent Objective nullified in child on delete. [#341]
- Deprecate various hasura default delete mutations. [#343]

### Fixed

- Fix IH issue: no longer creating another global tenant id. [#344]
- Fix IH issue: patch updating the integration. [#345]

## [4.3.3] - 2021-05-12

### Changed

- Update `parent_objective_id` trigger self referential not allowed. [#337]
- Add session remove to all endpoints. [#339]

## [4.3.2] - 2021-05-11

### Changed

- Migrated objective editing level null fields to default. [#335]

## [4.3.1] - 2021-05-10

### Changed

- Changed default for `objective_editing_levels`. [#333]

## [4.3.0] - 2021-05-07

### Added

- Add Hasura object relationship between `activity_logs` and `work_items`. [#327]
- Add task to clone hasura permissions en masse. [#325]
- Add required fields and passive deletes to okr fields. [#329]
- Add custom delete actions. [#324]
- Add `context_ids` param to the `current_user` endpoint. [#331]

### Changed

- Add a case for `none`/`noAccess` for Boards for which the user has no access. [#328]
- Changed db queries for more robust access during cascading deletes. [#330]

## [4.2.5] - 2021-04-29

### Fixed

- Comment broken migration for trigger cleanup. [#322]
- Fixed insert permissions issues for `objective_editing_levels`. [#323]

### Added

- Add `ActivityLog`s to the seeder. [#321]

## [4.2.4] - 2021-04-21

### Fixed

- Fixed broken migration that was stopping deployment. [#319]

### Changed

- `current_user` only returns relevant WorkItemContainer Roles. [#318]

## [4.2.3] - 2021-04-15

### Added

- Add `current_user` custom action in Hasura. [#314]
- Add `objective_editing_levels` to `WorkItemContainer`. [#317]

### Changed

- Change "Value Stream" to "Portfolio" in default levels. [#313]

### Fixed

- Add `Session.remove` to the end of the events action. [#315]

## [4.2.2] - 2021-04-13

### Changed

- Set `level_depth_default` on WorkItemContainers in `connect_activities`. [#310]
- Change Integration Hub admin functions to use `ADMIN_IH_DOMAIN`. [#311]

## [4.2.1] - 2021-04-12

### Added

- Add event handler for orphaned WorkItemContainers. [#306]
- Allow `app_owned_by` columns to be modified by a user role. [#307]
- Add a migration to remove orphaned WorkItemContainers. [#308]

## [4.2.0] - 2021-04-08

### Added

- Update the payloads for the `info` column in activity logs. [#286]
- Add event handler for orphan `WorkItem` cleanup. [#290]
- Add sqlalchemy mixin for timestamps. [#293]
- Add Sentry release support to to deployment. [#294]
- Add sentry additional data to failing token auth. [#296]

### Fixed

- Fix issue with duplicate `WorkItemContainer` creation. [#292]

### Changed

- Change the event trigger cleanup migration generator. [#298]

## [4.1.0] - 2021-04-06

### Changed

- Change the string that populates `action` in `activity_logs`. [#276]

### Fixed

- Add missing `external_title` field for new KR-WI mappings. [#273]
- Add a trigger for `check_child_objectives_level_depth`. [#277]
- Fix issues with custom actions not adding necessary data. [#280]
- Fix async/await issues in the Settings Insert operation. [#282]
- Fix global tenant id finder in staging/production. [#283]
- Fix race condition in event handlers. [#284]

### Added

- Add app user info to ActivityLogs when creating them. [#272]
- Add a task to create migrations for deleted hasura event triggers. [#279]
- Add `ih_global_tenant_id` field to the `settings` table. [#281]
- Add support for new integration hub methods in staging/production. [#285]

## [4.0.0] - 2021-03-25

### Added

- Add SQLAlchemy intregrations for Sentry. [#269]

### Fixed

- Fix issues relating to empty dict returned on empty searches. [#264]
- Fix activity log issues when there was no KeyResult. [#266]
- Fix unused `case_sensitive` setting from engine settings. [#267]
- Fix unused kwargs for sessionmaker. [#268]

### Changed

- Upgrade SQLAlchemy and engine parameters. [#265]

## [3.10.0] - 2021-03-18

### Added

- Add new fields `app_created_by` and `app_owner_id` to various tables. [#253]
- Add global tenant id setup for Integration Hub. [#255]
- Add new field `app_last_updated_by` to all tables. [#256]
- Add activity log events and handlers. [#262]
- Add a trigger to objectives to make sure level_depth is valid. [#263]

### Changed

- Change the dispatcher to use the `x-handler-module` header to find modules. [#259]
- Change the `level_depth` in `objectives` to be required. [#260]

## [3.9.0] - 2021-03-10

### Fixed

- Fix issues relating to cascading deletes and progress calculations. [#248]
- Add pessimistic connection pooling. [#251]

### Added

- Add an event handler for the settings table. [#240]
- Add the `search_users` custom action for Hasura. [#246]
- Add read permissions to `level_depth_default` field to the User role. [#247]
- Add update permissions to  `level_depth_default` field to the User role. [#249]
- Add insert permissions to  `level_depth_default` field to the User role. [#250]

### Changed

- Refactored the events dispatcher and handlers. [#241]
- Made errors in events controller, by default, to go to Sentry. [#242]

## [3.8.0] - 2021-02-24

### Added

- Add `activity_logs` table. [#226]
- Add validation of `level_depth_default` for `work_item_containers`. [#231]
- Add custom action `update_level_config`. [#234]
- Modify the generate_jwt task to include an env parameter. [#235]

### Changed

- Changed `level_configs` to `settings` table with `level_config` field. [#224]
- Changed `tenant_id_str` to be unique in `settings` table. [#227]
- Change parsing of `tenant_code` when creating IntHub registration. [#229]

## [3.7.0] - 2021-02-10

### Added

- Added request url of external api on failure. [#217]
- Added a Hasura event hook for `WorkItemContainer` INSERTs. [#218]
- Added customizable `InputParser` validations per endpoint. [#219]

### Changed

- Changed the service wrangler and adapters to use service proxies. [#210]

## [3.6.2] - 2021-02-04

### Fixed

- Fixed the unique constraint for work_items and work_item_containers. [#214]

## [3.6.1] - 2021-02-03

### Added

- Added an input prepper, to validate input data and authentication. [#206]

### Fixed

- Fixed corner-case wherein a progress point does not have a key result. [#205]
- Fixed missing required parameters in graphql schema and openapi spec. [#208]

### Changed

- Changed the `external_type` fields to use the product type. [#209]
- Changed the `external_type` fields to re-populate. [#211]

## [3.6.0] - 2021-01-25

### Added

- Added the `item_type` to results of `create_activity` action. [#199]
- Added a tool to re-sync work items with no Integration Hub subscription. [#196]

### Fixed

- Fixed issue with LKs JWT expiration time and timezones. [#202]

## [3.5.4] - 2021-01-20

### Added

- Added Integration Hub columns and logging. [#194]

## [3.5.3] - 2021-01-19

### Fixed

- Fixed issue with nullable KeyResult values causing errors. [#191]

## [3.5.2] - 2021-01-13

### Fixed

- Fixed issue with progress percentages not calculating. [#187]

## [3.4.6] - 2021-01-13

### Added

- Added better error handling to the Integration Hub subscription process. [#175]

## [3.4.5] - 2021-01-12

### Added

- Added `tenant_id_str` for the items created in the connect action. [#149]
- Added `tenant_id_str` as an indexed field to all tables. [#129]
- Updated `user` role permissions filtered by `tenant_id_str`. [#132]
- Added `tenant_id_str` column to the views. [#132]
- Added `list-activity-types` endpoint. [#134]
- Added Sentry for exception handling. [#135]
- Added retry when creating an activity. [#145]

### Changed

- Changed all subdomain references to domain. (full hostname) [#159]
- Changed the deployment tasks to account for environment and region. [#166]

### Fixed

- Fixed `tenant_id_str` issues for WorkItems and Key Result Mappings. [#163]
- Make sure KR prog % is between 0 and 100 when calculating O prog %. [#164]

## [3.4.4] - 2020-12-18

### Fixed

- Fixed settings environment variable collision. [#121]

## [3.4.3] - 2020-12-18

### Fixed

- Fixed objective percentage calculation. [#115]

### Added

- Added `external_title` field to `work_item_containers` table. [#114]

## [3.4.2] - 2020-12-03

### Fixed

- Fixed the dependencies. [#101] [#103]

## [3.4.1] - 2020-12-02

### Fixed

- Fixed the Docker image for production. [#100]

## [3.4.0] - 2020-12-02

### Added

- Created new invoke task `timestamp_migration` to easily add auto-updating
  `created_at` and `updated_at` fields to tables. [#88]
- Added POST /api/actions/search_activity_containers endpoint to search LeanKit
  boards, and corresponding resolver to Hasura as a custom action. [#91]

### Fixed

- Fixed recreation of foreign keys that was removing cascading deletions. [#81]

## [3.3.0] - 2020-11-20

### Added

- Added `key_result_progress_percentage` and `objective_progress_percentage`
  to progress points table. [#78]
- Added a Hasura event handler for key results. [#69]
- Turned `measured_at` field for Progress Points to required. [#76]
- Created a unique composite index on progress_points for `key_result_id`
  and `measured_at`. [#76]
- Added Hasura actions for searching and creating activities and
  their work item(s). [#71], [#77]

## [3.2.1] - 2020-11-04

### Fixed

- Adjusted the project settings for production. [#62]

## [3.2.0] - 2020-11-04

### Added

- Added settings to the dispatcher. [#60]

## [3.1.0] - 2020-11-02

### Added

- Added a health check endpoint. [#36]

### Changed

- Change seeder to not duplicate work_items associated with a key_result. [#43]

### Fixed

- Fixed tasks in order to support multiple environments.
  [#34] [#39] [#40] [#41] [#42]

## [3.0.0] - 2020-10-15

### Added

- Added several database views. [#10], [#16]
- Added new fields to the openapi.yml file. [#8], [#12]

### Changed

- Fixed the Hasura Metadata upload. [#13]

[//]: # "Release & PR links"
[3.0.0]: https://github.com/pv-platforma/okrs-api/releases/tag/3.0.0
[3.1.0]: https://github.com/pv-platforma/okrs-api/releases/tag/3.1.0
[3.2.0]: https://github.com/pv-platforma/okrs-api/releases/tag/3.2.0
[3.2.1]: https://github.com/pv-platforma/okrs-api/releases/tag/3.2.1
[3.3.0]: https://github.com/pv-platforma/okrs-api/releases/tag/3.3.0
[3.4.0]: https://github.com/pv-platforma/okrs-api/releases/tag/3.4.0
[3.4.1]: https://github.com/pv-platforma/okrs-api/releases/tag/3.4.1
[3.4.2]: https://github.com/pv-platforma/okrs-api/releases/tag/3.4.2
[3.4.3]: https://github.com/pv-platforma/okrs-api/releases/tag/3.4.3
[3.4.4]: https://github.com/pv-platforma/okrs-api/releases/tag/3.4.4
[3.4.5]: https://github.com/pv-platforma/okrs-api/releases/tag/3.4.5
[3.4.6]: https://github.com/pv-platforma/okrs-api/releases/tag/3.4.6
[3.5.2]: https://github.com/pv-platforma/okrs-api/releases/tag/3.5.2
[3.5.3]: https://github.com/pv-platforma/okrs-api/releases/tag/3.5.3
[3.5.4]: https://github.com/pv-platforma/okrs-api/releases/tag/3.5.4
[3.6.0]: https://github.com/pv-platforma/okrs-api/releases/tag/3.6.0
[3.6.1]: https://github.com/pv-platforma/okrs-api/releases/tag/3.6.1
[3.6.2]: https://github.com/pv-platforma/okrs-api/releases/tag/3.6.2
[3.7.0]: https://github.com/pv-platforma/okrs-api/releases/tag/3.7.0
[3.8.0]: https://github.com/pv-platforma/okrs-api/releases/tag/3.8.0
[3.9.0]: https://github.com/pv-platforma/okrs-api/releases/tag/3.9.0
[3.10.0]: https://github.com/pv-platforma/okrs-api/releases/tag/3.10.0
[4.0.0]: https://github.com/pv-platforma/okrs-api/releases/tag/4.0.0
[4.1.0]: https://github.com/pv-platforma/okrs-api/releases/tag/4.1.0
[4.2.0]: https://github.com/pv-platforma/okrs-api/releases/tag/4.2.0
[4.2.1]: https://github.com/pv-platforma/okrs-api/releases/tag/4.2.1
[4.2.2]: https://github.com/pv-platforma/okrs-api/releases/tag/4.2.2
[4.2.3]: https://github.com/pv-platforma/okrs-api/releases/tag/4.2.3
[4.2.4]: https://github.com/pv-platforma/okrs-api/releases/tag/4.2.4
[4.2.5]: https://github.com/pv-platforma/okrs-api/releases/tag/4.2.5
[4.3.0]: https://github.com/pv-platforma/okrs-api/releases/tag/4.3.0
[4.3.1]: https://github.com/pv-platforma/okrs-api/releases/tag/4.3.1
[4.3.2]: https://github.com/pv-platforma/okrs-api/releases/tag/4.3.2
[4.3.3]: https://github.com/pv-platforma/okrs-api/releases/tag/4.3.3
[4.4.0]: https://github.com/pv-platforma/okrs-api/releases/tag/4.4.0
[4.4.1]: https://github.com/pv-platforma/okrs-api/releases/tag/4.4.1
[4.4.2]: https://github.com/pv-platforma/okrs-api/releases/tag/4.4.2
[4.5.0]: https://github.com/pv-platforma/okrs-api/releases/tag/4.5.0
[4.5.1]: https://github.com/pv-platforma/okrs-api/releases/tag/4.5.1
[4.5.2]: https://github.com/pv-platforma/okrs-api/releases/tag/4.5.2
[4.6.0]: https://github.com/pv-platforma/okrs-api/releases/tag/4.6.0
[4.6.1]: https://github.com/pv-platforma/okrs-api/releases/tag/4.6.1
[4.6.2]: https://github.com/pv-platforma/okrs-api/releases/tag/4.6.2
[4.6.3]: https://github.com/pv-platforma/okrs-api/releases/tag/4.6.3
[4.6.4]: https://github.com/pv-platforma/okrs-api/releases/tag/4.6.4
[4.6.5]: https://github.com/pv-platforma/okrs-api/releases/tag/4.6.5
[4.6.6]: https://github.com/pv-platforma/okrs-api/releases/tag/4.6.6
[4.6.7]: https://github.com/pv-platforma/okrs-api/releases/tag/4.6.7
[4.7.0]: https://github.com/pv-platforma/okrs-api/releases/tag/4.7.0
[5.0.0]: https://github.com/pv-platforma/okrs-api/releases/tag/5.0.0
[#8]: https://github.com/pv-platforma/okrs-api/pull/8
[#12]: https://github.com/pv-platforma/okrs-api/pull/12
[#16]: https://github.com/pv-platforma/okrs-api/pull/16
[#10]: https://github.com/pv-platforma/okrs-api/pull/10
[#13]: https://github.com/pv-platforma/okrs-api/pull/13
[#34]: https://github.com/pv-platforma/okrs-api/pull/34
[#36]: https://github.com/pv-platforma/okrs-api/pull/36
[#39]: https://github.com/pv-platforma/okrs-api/pull/39
[#40]: https://github.com/pv-platforma/okrs-api/pull/40
[#41]: https://github.com/pv-platforma/okrs-api/pull/41
[#42]: https://github.com/pv-platforma/okrs-api/pull/42
[#43]: https://github.com/pv-platforma/okrs-api/pull/43
[#60]: https://github.com/pv-platforma/okrs-api/pull/60
[#62]: https://github.com/pv-platforma/okrs-api/pull/62
[#69]: https://github.com/pv-platforma/okrs-api/pull/69
[#71]: https://github.com/pv-platforma/okrs-api/pull/76
[#76]: https://github.com/pv-platforma/okrs-api/pull/76
[#77]: https://github.com/pv-platforma/okrs-api/pull/77
[#78]: https://github.com/pv-platforma/okrs-api/pull/78
[#81]: https://github.com/pv-platforma/okrs-api/pull/81
[#88]: https://github.com/pv-platforma/okrs-api/pull/88
[#91]: https://github.com/pv-platforma/okrs-api/pull/91
[#100]: https://github.com/pv-platforma/okrs-api/pull/100
[#101]: https://github.com/pv-platforma/okrs-api/pull/101
[#103]: https://github.com/pv-platforma/okrs-api/pull/103
[#114]: https://github.com/pv-platforma/okrs-api/pull/114
[#115]: https://github.com/pv-platforma/okrs-api/pull/115
[#121]: https://github.com/pv-platforma/okrs-api/pull/121
[#129]: https://github.com/pv-platforma/okrs-api/pull/129
[#132]: https://github.com/pv-platforma/okrs-api/pull/132
[#134]: https://github.com/pv-platforma/okrs-api/pull/134
[#135]: https://github.com/pv-platforma/okrs-api/pull/135
[#145]: https://github.com/pv-platforma/okrs-api/pull/145
[#149]: https://github.com/pv-platforma/okrs-api/pull/149
[#159]: https://github.com/pv-platforma/okrs-api/pull/159
[#163]: https://github.com/pv-platforma/okrs-api/pull/163
[#164]: https://github.com/pv-platforma/okrs-api/pull/164
[#166]: https://github.com/pv-platforma/okrs-api/pull/166
[#175]: https://github.com/pv-platforma/okrs-api/pull/175
[#187]: https://github.com/pv-platforma/okrs-api/pull/187
[#191]: https://github.com/pv-platforma/okrs-api/pull/191
[#194]: https://github.com/pv-platforma/okrs-api/pull/194
[#196]: https://github.com/pv-platforma/okrs-api/pull/196
[#199]: https://github.com/pv-platforma/okrs-api/pull/199
[#202]: https://github.com/pv-platforma/okrs-api/pull/202
[#205]: https://github.com/pv-platforma/okrs-api/pull/205
[#206]: https://github.com/pv-platforma/okrs-api/pull/206
[#208]: https://github.com/pv-platforma/okrs-api/pull/208
[#209]: https://github.com/pv-platforma/okrs-api/pull/209
[#210]: https://github.com/pv-platforma/okrs-api/pull/210
[#211]: https://github.com/pv-platforma/okrs-api/pull/211
[#214]: https://github.com/pv-platforma/okrs-api/pull/214
[#217]: https://github.com/pv-platforma/okrs-api/pull/217
[#218]: https://github.com/pv-platforma/okrs-api/pull/218
[#219]: https://github.com/pv-platforma/okrs-api/pull/219
[#224]: https://github.com/pv-platforma/okrs-api/pull/224
[#226]: https://github.com/pv-platforma/okrs-api/pull/226
[#227]: https://github.com/pv-platforma/okrs-api/pull/227
[#229]: https://github.com/pv-platforma/okrs-api/pull/229
[#231]: https://github.com/pv-platforma/okrs-api/pull/231
[#234]: https://github.com/pv-platforma/okrs-api/pull/234
[#235]: https://github.com/pv-platforma/okrs-api/pull/235
[#240]: https://github.com/pv-platforma/okrs-api/pull/240
[#241]: https://github.com/pv-platforma/okrs-api/pull/241
[#242]: https://github.com/pv-platforma/okrs-api/pull/242
[#246]: https://github.com/pv-platforma/okrs-api/pull/246
[#247]: https://github.com/pv-platforma/okrs-api/pull/247
[#248]: https://github.com/pv-platforma/okrs-api/pull/248
[#249]: https://github.com/pv-platforma/okrs-api/pull/249
[#250]: https://github.com/pv-platforma/okrs-api/pull/250
[#251]: https://github.com/pv-platforma/okrs-api/pull/251
[#253]: https://github.com/pv-platforma/okrs-api/pull/253
[#255]: https://github.com/pv-platforma/okrs-api/pull/255
[#256]: https://github.com/pv-platforma/okrs-api/pull/256
[#259]: https://github.com/pv-platforma/okrs-api/pull/259
[#260]: https://github.com/pv-platforma/okrs-api/pull/260
[#262]: https://github.com/pv-platforma/okrs-api/pull/262
[#263]: https://github.com/pv-platforma/okrs-api/pull/263
[#264]: https://github.com/pv-platforma/okrs-api/pull/264
[#265]: https://github.com/pv-platforma/okrs-api/pull/265
[#266]: https://github.com/pv-platforma/okrs-api/pull/266
[#267]: https://github.com/pv-platforma/okrs-api/pull/267
[#268]: https://github.com/pv-platforma/okrs-api/pull/268
[#269]: https://github.com/pv-platforma/okrs-api/pull/269
[#272]: https://github.com/pv-platforma/okrs-api/pull/272
[#273]: https://github.com/pv-platforma/okrs-api/pull/273
[#276]: https://github.com/pv-platforma/okrs-api/pull/276
[#277]: https://github.com/pv-platforma/okrs-api/pull/277
[#279]: https://github.com/pv-platforma/okrs-api/pull/279
[#280]: https://github.com/pv-platforma/okrs-api/pull/280
[#281]: https://github.com/pv-platforma/okrs-api/pull/281
[#282]: https://github.com/pv-platforma/okrs-api/pull/282
[#283]: https://github.com/pv-platforma/okrs-api/pull/283
[#284]: https://github.com/pv-platforma/okrs-api/pull/284
[#285]: https://github.com/pv-platforma/okrs-api/pull/285
[#286]: https://github.com/pv-platforma/okrs-api/pull/286
[#290]: https://github.com/pv-platforma/okrs-api/pull/290
[#292]: https://github.com/pv-platforma/okrs-api/pull/292
[#293]: https://github.com/pv-platforma/okrs-api/pull/293
[#294]: https://github.com/pv-platforma/okrs-api/pull/294
[#296]: https://github.com/pv-platforma/okrs-api/pull/296
[#298]: https://github.com/pv-platforma/okrs-api/pull/298
[#306]: https://github.com/pv-platforma/okrs-api/pull/306
[#307]: https://github.com/pv-platforma/okrs-api/pull/307
[#308]: https://github.com/pv-platforma/okrs-api/pull/308
[#310]: https://github.com/pv-platforma/okrs-api/pull/310
[#311]: https://github.com/pv-platforma/okrs-api/pull/311
[#313]: https://github.com/pv-platforma/okrs-api/pull/313
[#314]: https://github.com/pv-platforma/okrs-api/pull/314
[#315]: https://github.com/pv-platforma/okrs-api/pull/315
[#317]: https://github.com/pv-platforma/okrs-api/pull/317
[#318]: https://github.com/pv-platforma/okrs-api/pull/318
[#319]: https://github.com/pv-platforma/okrs-api/pull/319
[#321]: https://github.com/pv-platforma/okrs-api/pull/321
[#322]: https://github.com/pv-platforma/okrs-api/pull/322
[#323]: https://github.com/pv-platforma/okrs-api/pull/323
[#324]: https://github.com/pv-platforma/okrs-api/pull/324
[#325]: https://github.com/pv-platforma/okrs-api/pull/325
[#327]: https://github.com/pv-platforma/okrs-api/pull/327
[#328]: https://github.com/pv-platforma/okrs-api/pull/328
[#329]: https://github.com/pv-platforma/okrs-api/pull/329
[#330]: https://github.com/pv-platforma/okrs-api/pull/330
[#331]: https://github.com/pv-platforma/okrs-api/pull/331
[#333]: https://github.com/pv-platforma/okrs-api/pull/333
[#335]: https://github.com/pv-platforma/okrs-api/pull/335
[#337]: https://github.com/pv-platforma/okrs-api/pull/337
[#338]: https://github.com/pv-platforma/okrs-api/pull/338
[#339]: https://github.com/pv-platforma/okrs-api/pull/339
[#341]: https://github.com/pv-platforma/okrs-api/pull/341
[#342]: https://github.com/pv-platforma/okrs-api/pull/342
[#343]: https://github.com/pv-platforma/okrs-api/pull/343
[#344]: https://github.com/pv-platforma/okrs-api/pull/344
[#345]: https://github.com/pv-platforma/okrs-api/pull/345
[#347]: https://github.com/pv-platforma/okrs-api/pull/347
[#351]: https://github.com/pv-platforma/okrs-api/pull/351
[#352]: https://github.com/pv-platforma/okrs-api/pull/352
[#354]: https://github.com/pv-platforma/okrs-api/pull/354
[#355]: https://github.com/pv-platforma/okrs-api/pull/355
[#358]: https://github.com/pv-platforma/okrs-api/pull/358
[#359]: https://github.com/pv-platforma/okrs-api/pull/359
[#360]: https://github.com/pv-platforma/okrs-api/pull/360
[#361]: https://github.com/pv-platforma/okrs-api/pull/361
[#363]: https://github.com/pv-platforma/okrs-api/pull/363
[#364]: https://github.com/pv-platforma/okrs-api/pull/364
[#366]: https://github.com/pv-platforma/okrs-api/pull/366
[#367]: https://github.com/pv-platforma/okrs-api/pull/367
[#369]: https://github.com/pv-platforma/okrs-api/pull/369
[#370]: https://github.com/pv-platforma/okrs-api/pull/370
[#371]: https://github.com/pv-platforma/okrs-api/pull/371
[#373]: https://github.com/pv-platforma/okrs-api/pull/373
[#374]: https://github.com/pv-platforma/okrs-api/pull/374
[#375]: https://github.com/pv-platforma/okrs-api/pull/375
[#376]: https://github.com/pv-platforma/okrs-api/pull/376
[#377]: https://github.com/pv-platforma/okrs-api/pull/377
[#381]: https://github.com/pv-platforma/okrs-api/pull/381
[#382]: https://github.com/pv-platforma/okrs-api/pull/382
[#383]: https://github.com/pv-platforma/okrs-api/pull/383
[#384]: https://github.com/pv-platforma/okrs-api/pull/384
[#385]: https://github.com/pv-platforma/okrs-api/pull/385
[#386]: https://github.com/pv-platforma/okrs-api/pull/386
[#387]: https://github.com/pv-platforma/okrs-api/pull/387
[#391]: https://github.com/pv-platforma/okrs-api/pull/391
[#393]: https://github.com/pv-platforma/okrs-api/pull/393
[#395]: https://github.com/pv-platforma/okrs-api/pull/395
[#398]: https://github.com/pv-platforma/okrs-api/pull/398
[#399]: https://github.com/pv-platforma/okrs-api/pull/399
[#401]: https://github.com/pv-platforma/okrs-api/pull/401
[#402]: https://github.com/pv-platforma/okrs-api/pull/402
[#403]: https://github.com/pv-platforma/okrs-api/pull/403
[#405]: https://github.com/pv-platforma/okrs-api/pull/405
[#406]: https://github.com/pv-platforma/okrs-api/pull/406
[#408]: https://github.com/pv-platforma/okrs-api/pull/408
[#411]: https://github.com/pv-platforma/okrs-api/pull/411
[#412]: https://github.com/pv-platforma/okrs-api/pull/412
[#415]: https://github.com/pv-platforma/okrs-api/pull/415
[#422]: https://github.com/pv-platforma/okrs-api/pull/422
[#426]: https://github.com/pv-platforma/okrs-api/pull/426
[#429]: https://github.com/pv-platforma/okrs-api/pull/429
[#431]: https://github.com/pv-platforma/okrs-api/pull/431
[#440]: https://github.com/pv-platforma/okrs-api/pull/440
[#441]: https://github.com/pv-platforma/okrs-api/pull/441
[#442]: https://github.com/pv-platforma/okrs-api/pull/442
[#443]: https://github.com/pv-platforma/okrs-api/pull/443
[#444]: https://github.com/pv-platforma/okrs-api/pull/444
[#445]: https://github.com/pv-platforma/okrs-api/pull/445
[#448]: https://github.com/pv-platforma/okrs-api/pull/448
[#453]: https://github.com/pv-platforma/okrs-api/pull/453
[#454]: https://github.com/pv-platforma/okrs-api/pull/454
[#462]: https://github.com/pv-platforma/okrs-api/pull/462
[#463]: https://github.com/pv-platforma/okrs-api/pull/463
[#465]: https://github.com/pv-platforma/okrs-api/pull/465
[#468]: https://github.com/pv-platforma/okrs-api/pull/468
[#469]: https://github.com/pv-platforma/okrs-api/pull/469
[#471]: https://github.com/pv-platforma/okrs-api/pull/471
[#473]: https://github.com/pv-platforma/okrs-api/pull/473
[#474]: https://github.com/pv-platforma/okrs-api/pull/474
[#475]: https://github.com/pv-platforma/okrs-api/pull/475
[#476]: https://github.com/pv-platforma/okrs-api/pull/476
[#478]: https://github.com/pv-platforma/okrs-api/pull/478
[#480]: https://github.com/pv-platforma/okrs-api/pull/480
[#481]: https://github.com/pv-platforma/okrs-api/pull/481
[#482]: https://github.com/pv-platforma/okrs-api/pull/482
[#485]: https://github.com/pv-platforma/okrs-api/pull/485
[#486]: https://github.com/pv-platforma/okrs-api/pull/486
[#487]: https://github.com/pv-platforma/okrs-api/pull/487
[#489]: https://github.com/pv-platforma/okrs-api/pull/489
[#490]: https://github.com/pv-platforma/okrs-api/pull/490
[#491]: https://github.com/pv-platforma/okrs-api/pull/491
[#492]: https://github.com/pv-platforma/okrs-api/pull/492
[#493]: https://github.com/pv-platforma/okrs-api/pull/493
[#494]: https://github.com/pv-platforma/okrs-api/pull/494
[#495]: https://github.com/pv-platforma/okrs-api/pull/495
[#496]: https://github.com/pv-platforma/okrs-api/pull/496
[#497]: https://github.com/pv-platforma/okrs-api/pull/497
[#498]: https://github.com/pv-platforma/okrs-api/pull/498
[#499]: https://github.com/pv-platforma/okrs-api/pull/499
[#501]: https://github.com/pv-platforma/okrs-api/pull/501
[#502]: https://github.com/pv-platforma/okrs-api/pull/502
[#503]: https://github.com/pv-platforma/okrs-api/pull/503
[#504]: https://github.com/pv-platforma/okrs-api/pull/504
[#505]: https://github.com/pv-platforma/okrs-api/pull/505
[#506]: https://github.com/pv-platforma/okrs-api/pull/506
[#507]: https://github.com/pv-platforma/okrs-api/pull/507
[#508]: https://github.com/pv-platforma/okrs-api/pull/508
[#509]: https://github.com/pv-platforma/okrs-api/pull/509
[#510]: https://github.com/pv-platforma/okrs-api/pull/510
[#511]: https://github.com/pv-platforma/okrs-api/pull/511
[#512]: https://github.com/pv-platforma/okrs-api/pull/512
[#513]: https://github.com/pv-platforma/okrs-api/pull/513
[#514]: https://github.com/pv-platforma/okrs-api/pull/514
[#515]: https://github.com/pv-platforma/okrs-api/pull/515
[#516]: https://github.com/pv-platforma/okrs-api/pull/516
[#517]: https://github.com/pv-platforma/okrs-api/pull/517
[#518]: https://github.com/pv-platforma/okrs-api/pull/518
[#519]: https://github.com/pv-platforma/okrs-api/pull/519
[#520]: https://github.com/pv-platforma/okrs-api/pull/520
[#521]: https://github.com/pv-platforma/okrs-api/pull/521
[#522]: https://github.com/pv-platforma/okrs-api/pull/522
[#523]: https://github.com/pv-platforma/okrs-api/pull/523
[#524]: https://github.com/pv-platforma/okrs-api/pull/524
[#525]: https://github.com/pv-platforma/okrs-api/pull/525
[#526]: https://github.com/pv-platforma/okrs-api/pull/526
[#528]: https://github.com/pv-platforma/okrs-api/pull/528
[#529]: https://github.com/pv-platforma/okrs-api/pull/529
[#530]: https://github.com/pv-platforma/okrs-api/pull/530
[#534]: https://github.com/pv-platforma/okrs-api/pull/534
[#535]: https://github.com/pv-platforma/okrs-api/pull/535
[#536]: https://github.com/pv-platforma/okrs-api/pull/536
[#537]: https://github.com/pv-platforma/okrs-api/pull/537
[#538]: https://github.com/pv-platforma/okrs-api/pull/538
[#539]: https://github.com/pv-platforma/okrs-api/pull/539
[#540]: https://github.com/pv-platforma/okrs-api/pull/540
[#541]: https://github.com/pv-platforma/okrs-api/pull/541
[#542]: https://github.com/pv-platforma/okrs-api/pull/542
[#543]: https://github.com/pv-platforma/okrs-api/pull/543
[#544]: https://github.com/pv-platforma/okrs-api/pull/544
[#545]: https://github.com/pv-platforma/okrs-api/pull/545
[#546]: https://github.com/pv-platforma/okrs-api/pull/546
[#547]: https://github.com/pv-platforma/okrs-api/pull/547
[#548]: https://github.com/pv-platforma/okrs-api/pull/548
[#549]: https://github.com/pv-platforma/okrs-api/pull/549
[#550]: https://github.com/pv-platforma/okrs-api/pull/550
[#551]: https://github.com/pv-platforma/okrs-api/pull/551
[#553]: https://github.com/pv-platforma/okrs-api/pull/553
[#560]: https://github.com/pv-platforma/okrs-api/pull/560
[#555]: https://github.com/pv-platforma/okrs-api/pull/555
[#557]: https://github.com/pv-platforma/okrs-api/pull/557
[#561]: https://github.com/pv-platforma/okrs-api/pull/561
[#562]: https://github.com/pv-platforma/okrs-api/pull/562
[#563]: https://github.com/pv-platforma/okrs-api/pull/563
[#564]: https://github.com/pv-platforma/okrs-api/pull/564
[#565]: https://github.com/pv-platforma/okrs-api/pull/565
[#567]: https://github.com/pv-platforma/okrs-api/pull/567
[#568]: https://github.com/pv-platforma/okrs-api/pull/568
[#569]: https://github.com/pv-platforma/okrs-api/pull/569
[#571]: https://github.com/pv-platforma/okrs-api/pull/571
[#572]: https://github.com/pv-platforma/okrs-api/pull/572
[#573]: https://github.com/pv-platforma/okrs-api/pull/573
[#574]: https://github.com/pv-platforma/okrs-api/pull/574
[#575]: https://github.com/pv-platforma/okrs-api/pull/575
[#580]: https://github.com/pv-platforma/okrs-api/pull/580
[#581]: https://github.com/pv-platforma/okrs-api/pull/581
[#582]: https://github.com/pv-platforma/okrs-api/pull/582
[#583]: https://github.com/pv-platforma/okrs-api/pull/583
[#584]: https://github.com/pv-platforma/okrs-api/pull/584
[#585]: https://github.com/pv-platforma/okrs-api/pull/585
[#586]: https://github.com/pv-platforma/okrs-api/pull/586
[#588]: https://github.com/pv-platforma/okrs-api/pull/588
[#591]: https://github.com/pv-platforma/okrs-api/pull/591
[#592]: https://github.com/pv-platforma/okrs-api/pull/592
[#593]: https://github.com/pv-platforma/okrs-api/pull/593
[#594]: https://github.com/pv-platforma/okrs-api/pull/594
[#600]: https://github.com/pv-platforma/okrs-api/pull/600
[#645]: https://github.com/pv-platforma/okrs-api/pull/645
[#646]: https://github.com/pv-platforma/okrs-api/pull/646
[#647]: https://github.com/pv-platforma/okrs-api/pull/647
[#648]: https://github.com/pv-platforma/okrs-api/pull/648
[#649]: https://github.com/pv-platforma/okrs-api/pull/649
[#650]: https://github.com/pv-platforma/okrs-api/pull/650
[#651]: https://github.com/pv-platforma/okrs-api/pull/651
[#654]: https://github.com/pv-platforma/okrs-api/pull/654
[#669]: https://github.com/pv-platforma/okrs-api/pull/669
[#699]: https://github.com/pv-platforma/okrs-api/pull/699
[#723]: https://github.com/pv-platforma/okrs-api/pull/723
[#724]: https://github.com/pv-platforma/okrs-api/pull/724
[#728]: https://github.com/pv-platforma/okrs-api/pull/728
[#729]: https://github.com/pv-platforma/okrs-api/pull/729
[#738]: https://github.com/pv-platforma/okrs-api/pull/738
[#741]: https://github.com/pv-platforma/okrs-api/pull/741
[#749]: https://github.com/pv-platforma/okrs-api/pull/749
[#764]: https://github.com/pv-platforma/okrs-api/pull/764
[#774]: https://github.com/pv-platforma/okrs-api/pull/774
[#788]: https://github.com/pv-platforma/okrs-api/pull/788
[#794]: https://github.com/pv-platforma/okrs-api/pull/794
[#811]: https://github.com/pv-platforma/okrs-api/pull/811
[#818]: https://github.com/pv-platforma/okrs-api/pull/818
[#823]: https://github.com/pv-platforma/okrs-api/pull/823
[#825]: https://github.com/pv-platforma/okrs-api/pull/826
[#813]: https://github.com/pv-platforma/okrs-api/pull/813
[#849]: https://github.com/pv-platforma/okrs-api/pull/849
[#851]: https://github.com/pv-platforma/okrs-api/pull/851
[#854]: https://github.com/pv-platforma/okrs-api/pull/854
[#856]: https://github.com/pv-platforma/okrs-api/pull/856
[#871]: https://github.com/pv-platforma/okrs-api/pull/871
[#850]: https://github.com/pv-platforma/okrs-api/pull/850
[#864]: https://github.com/pv-platforma/okrs-api/pull/864
[#881]: https://github.com/pv-platforma/okrs-api/pull/881
[#884]: https://github.com/pv-platforma/okrs-api/pull/884
[#888]: https://github.com/pv-platforma/okrs-api/pull/888
[#887]: https://github.com/pv-platforma/okrs-api/pull/887
[#889]: https://github.com/pv-platforma/okrs-api/pull/889
[#890]: https://github.com/pv-platforma/okrs-api/pull/890
[#892]: https://github.com/pv-platforma/okrs-api/pull/892
[#893]: https://github.com/pv-platforma/okrs-api/pull/893
[#896]: https://github.com/pv-platforma/okrs-api/pull/896
[#897]: https://github.com/pv-platforma/okrs-api/pull/897
[#902]: https://github.com/pv-platforma/okrs-api/pull/902
[#901]: https://github.com/pv-platforma/okrs-api/pull/901
[#898]: https://github.com/pv-platforma/okrs-api/pull/898
[#906]: https://github.com/pv-platforma/okrs-api/pull/906
[#911]: https://github.com/pv-platforma/okrs-api/pull/911
[#912]: https://github.com/pv-platforma/okrs-api/pull/912
[#913]: https://github.com/pv-platforma/okrs-api/pull/913
[#908]: https://github.com/pv-platforma/okrs-api/pull/908
[#918]: https://github.com/pv-platforma/okrs-api/pull/918
[#919]: https://github.com/pv-platforma/okrs-api/pull/919
[#915]: https://github.com/pv-platforma/okrs-api/pull/915
[#922]: https://github.com/pv-platforma/okrs-api/pull/922
[#927]: https://github.com/pv-platforma/okrs-api/pull/927
[#923]: https://github.com/pv-platforma/okrs-api/pull/923
[#934]: https://github.com/pv-platforma/okrs-api/pull/934
[#930]: https://github.com/pv-platforma/okrs-api/pull/930
[#938]: https://github.com/pv-platforma/okrs-api/pull/942
[#933]: https://github.com/pv-platforma/okrs-api/pull/933
[#932]: https://github.com/pv-platforma/okrs-api/pull/932
[#950]: https://github.com/pv-platforma/okrs-api/pull/950
[#951]: https://github.com/pv-platforma/okrs-api/pull/951
[#952]: https://github.com/pv-platforma/okrs-api/pull/952
[#949]: https://github.com/pv-platforma/okrs-api/pull/949
[#962]: https://github.com/pv-platforma/okrs-api/pull/962
[#966]: https://github.com/pv-platforma/okrs-api/pull/966
[#965]: https://github.com/pv-platforma/okrs-api/pull/965
[#968]: https://github.com/pv-platforma/okrs-api/pull/968
[#970]: https://github.com/pv-platforma/okrs-api/pull/970
[#960]: https://github.com/pv-platforma/okrs-api/pull/960
[#972]: https://github.com/pv-platforma/okrs-api/pull/972
[#974]: https://github.com/pv-platforma/okrs-api/pull/974
[#980]: https://github.com/pv-platforma/okrs-api/pull/980
[#985]: https://github.com/pv-platforma/okrs-api/pull/985
[#956]: https://github.com/pv-platforma/okrs-api/pull/956
[#989]: https://github.com/pv-platforma/okrs-api/pull/989
[#1002]: https://github.com/pv-platforma/okrs-api/pull/1002
[#1000]: https://github.com/pv-platforma/okrs-api/pull/1000
[#1008]: https://github.com/pv-platforma/okrs-api/pull/1008
[#1001]: https://github.com/pv-platforma/okrs-api/pull/1001
[#1005]: https://github.com/pv-platforma/okrs-api/pull/1005
[#1012]: https://github.com/pv-platforma/okrs-api/pull/1012
[#1018]: https://github.com/pv-platforma/okrs-api/pull/1018
[#998]: https://github.com/pv-platforma/okrs-api/pull/998
[#1017]: https://github.com/pv-platforma/okrs-api/pull/1017
[#1015]: https://github.com/pv-platforma/okrs-api/pull/1015
[#1010]: https://github.com/pv-platforma/okrs-api/pull/1010
[#1026]: https://github.com/pv-platforma/okrs-api/pull/1026
[#1027]: https://github.com/pv-platforma/okrs-api/pull/1027
[#1030]: https://github.com/pv-platforma/okrs-api/pull/1030
[#1034]: https://github.com/pv-platforma/okrs-api/pull/1034
[#1025]: https://github.com/pv-platforma/okrs-api/pull/1025
[#1019]: https://github.com/pv-platforma/okrs-api/pull/1019
[#1037]: https://github.com/pv-platforma/okrs-api/pull/1037
[#1038]: https://github.com/pv-platforma/okrs-api/pull/1038
[#1036]: https://github.com/pv-platforma/okrs-api/pull/1036
[#1045]: https://github.com/pv-platforma/okrs-api/pull/1045
[#1043]: https://github.com/pv-platforma/okrs-api/pull/1043
[#1050]: https://github.com/pv-platforma/okrs-api/pull/1050
[#1051]: https://github.com/pv-platforma/okrs-api/pull/1051
[#1069]: https://github.com/pv-platforma/okrs-api/pull/1069
[#1071]: https://github.com/pv-platforma/okrs-api/pull/1071
[#1059]: https://github.com/pv-platforma/okrs-api/pull/1059
[#1083]: https://github.com/pv-platforma/okrs-api/pull/1083
[#1091]: https://github.com/pv-platforma/okrs-api/pull/1091
[#1072]: https://github.com/pv-platforma/okrs-api/pull/1072
[#1093]: https://github.com/pv-platforma/okrs-api/pull/1093
[#1097]: https://github.com/pv-platforma/okrs-api/pull/1097
[#1096]: https://github.com/pv-platforma/okrs-api/pull/1096
[#1075]: https://github.com/pv-platforma/okrs-api/pull/1075
[#1121]: https://github.com/pv-platforma/okrs-api/pull/1121
[#1122]: https://github.com/pv-platforma/okrs-api/pull/1122
[#1117]: https://github.com/pv-platforma/okrs-api/pull/1117
