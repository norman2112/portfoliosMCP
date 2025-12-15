# Financial Plan API – Combined Requirements & Implementation Guide


---

## Financial Plan Requirements

Financial Plan Upsert Requirements Guide
1. Purpose
- Enable an MCP server to create or update a single capital expense line item.
- Use Planview IFinancialPlanService2 SOAP Upsert.
2. Requirements
- SOAP endpoint URL.
- Credentials (API token or basic auth).
- FinancialPlanKey or EntityKey.
- AccountKey for CAPEX.
- PeriodKey list or mapping.
- CurrencyKey.
- Value, Unit.
3. Process
- Build SOAP envelope with FinancialPlanDto.
- Include only one FinancialPlanLineDto for single-line load.
- Send via HTTP POST with text/xml.
- Parse SOAP response for faults.
4. Example Minimal Envelope
ekey://12/MyPlan
key://2/$Account/13607
key://1/USD
key://16/197
10000
Currency
5. MCP Integration Steps
- Add tool schema accepting planKey, accountKey, periodKey, value, currency.

- Build XML template.
- HTTP POST SOAP body.
- Return parsed result or error.
6. Notes
- Only changed or added lines must be sent.
- AccountKey and PeriodKey must match PV configuration.


---

## Financial Plan Update / Upsert Guide

IFinancialPlanService2
IFinancialPlanService2 W eb Service Interface
Description
Note : Review Getting Started with W eb Services befor e reading this document.
IFinancialPlanService2 is an interface to the FinancialPlanService web service that allows a user to r ead and upsert
financial plans.
Using this web service interface, one can perform the following actions:
•Create a new financial plan in Planview Enterprise One™. The model, and version, and accounts to be used with the
new financial plan must alr eady exist. In addition, the entity (pr ojects, or ganizational r esour ce, pr oduct, cost center ,
strategy , asset, or service) upon which the financial plan is based must also alr eady exist.
•Create new lines in a financial plan.
•Update existing lines.
•Export existing financials plans to another application.
The W eb Service Definition Language (WSDL) file for the FinancialPlanService can be obtained via the following URL:
http:// hostname /iisServer/Services/FinancialPlanService.svc?wsdl wher ehostname is the name (addr ess) of the machine
upon which Planview Enterprise One is installed and iisServer is the name of the virtual IIS server upon which the web
service r esides (typically this is planview). The service addr ess is the same URL without ?wsdl.
Grants and Featur es
GrantsGrants
Read:
•Read-write or r ead-only grant to the entity's structur e code.
Upsert:
•Read-write grant to the entity's structur e code.
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
1

FeaturFeatur es for Wes for W orkork
Read:
•View W ork Financial Plans (r eview_budget).
Upsert:
•Edit W ork Financial Plans (edit_budget).
•Any account or version level featur es.1,2
FeaturFeatur es for Strategieses for Strategies
Read:
•View Strategic Financial Plans (r eview_budget_strat).
Upsert:
•Edit Strategic Financial Plans (edit_budget_strat).
•Any account or version level featur es.1,2
FeaturFeatur es for Ores for Or ganizational Financial Plansganizational Financial Plans
Read:
•View Or ganizational Financial Plans (review_budget_or g).
Upsert:
•Edit Or ganizational Financial Plans (edit_budget_or g).
•Any account or version level featur es.1,2
FeaturFeatur es for Cost Center Financial Managementes for Cost Center Financial Management
Read:
•View Cost Center Financial Plans (view_cc_fp).
Upsert:
•Edit Cost Center Financial Plans (edit_cc_fp).
•Any account or version level featur es.1,2
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
2

FeaturFeatur es for Outcome Financial Managementes for Outcome Financial Management
Read:
•View Outcome Financial Plans (view_pr od_fp)
Upsert:
•Edit Outcome Financial Plans (edit_pr od_fp).
•Any account or version level featur es.1,2
RemarksRemarks
1If any account level featur es have been configur ed to r estrict editing of individual accounts these will also be needed
(Administration > System Configuration > Financial Management > Financial Planning > Financial Planning
Models -> click an action menu for a r owand then click Configure Accounts > Edit Feature column).
2If any version level featur es have been configur ed to r estrict editing of individual versions these will be needed
(Administration > System Configuration > Financial Management > Financial Planning > Financial Planning
Models > Configure Versions > Edit Version > Edit Rules > Edit Feature ).
Read:
•Featur es: The account featur e (fm_model_acct.edit_featur e) and the version featur e (fm_version.edit_featur e).
•Grants: Read/write or r ead only grant to the entity's structur e code.
Upsert:
•Grants: Read/write grant to the entity's structur e code.
SoapUI Read Examples
Read – Example 1: Read the Financial Plan Cr eated in Example 1 of SoapUI
Upsert Examples.
•Use the an eKey URI in the Key field to identify the financial plan.
Request
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
xmlns:ns="http://schemas.planview.com/PlanviewEnterprise/Services/FinancialPlan2/
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
3

2012/09"
xmlns:ns1="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/
FinancialPlanDto/2013/03"
xmlns:ns2="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/
FinancialPlanLineDto/2013/03"
xmlns:ns3="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/
LineAttributeDto/2012/09"
xmlns:ns4="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/EntryDto/
2010/01/01">
<soapenv:Header/>
<soapenv:Body>
<ns:Read>
<ns:dtos>
<ns1:FinancialPlanDto>
<ns1:Key>ekey://12/MyFinancialPlan/WorkPlan1</ns1:Key>
</ns1:FinancialPlanDto>
</ns:dtos>
</ns:Read>
</soapenv:Body>
</soapenv:Envelope>
ResponseResponse
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
<s:Body>
<ReadResponse xmlns="http://schemas.planview.com/PlanviewEnterprise/Services/
FinancialPlan2/2012/09">
<ReadResult xmlns:a="http://schemas.planview.com/PlanviewEnterprise/
OpenSuite/OpenSuiteResult/2010/01/01" xmlns:i="http://www.w3.org/2001/XMLSchema-
instance">
<a:Failures xmlns:b="http://schemas.planview.com/PlanviewEnterprise/
OpenSuite/OpenSuiteStatus/2010/01/01"/>
<a:GeneralErrorMessage i:nil="true"/>
<a:Successes xmlns:b="http://schemas.planview.com/PlanviewEnterprise/
OpenSuite/OpenSuiteStatus/2010/01/01">
<b:OpenSuiteStatus i:type="c:FinancialPlanStatus"
xmlns:c="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/
FinancialPlanStatus/2013/01">
<b:Code i:nil="true"/>
<b:ErrorMessage i:nil="true"/>
<b:SourceIndex>0</b:SourceIndex>
<c:Dto xmlns:d="http://schemas.planview.com/PlanviewEnterprise/
OpenSuite/Dtos/FinancialPlanDto/2013/03">
<d:EntityDescription>Project for a Financial Plan -
JMC</d:EntityDescription>
<d:EntityKey>key://2/$Plan/15410</d:EntityKey>
<d:Key>key://12/2898</d:Key>
<d:Lines xmlns:e="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/FinancialPlanLineDto/2013/03">
<!-- Benefit account -->
<!-- Benefit number of units -->
<e:FinancialPlanLineDto>
<e:AccountDescription>Investment
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
4

Benefit</e:AccountDescription>
<e:AccountKey>key://2/$Account/11089</e:AccountKey>
<e:AccountParentDescription>Benefit</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09">
<f:LineAttributeDto>
<f:AltStructureKey>key://2/AGR3/
1403</f:AltStructureKey>
<f:AltStrucutureDescription>ADP</f:AltStrucutureDescription>
</f:LineAttributeDto>
<f:LineAttributeDto>
<f:AltStructureKey>key://2/Cbs1/
11038</f:AltStructureKey>
<f:AltStrucutureDescription>0198
Networking</f:AltStrucutureDescription>
</f:LineAttributeDto>
</e:Attributes>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2012</f:PeriodDescription>
<f:PeriodKey>key://16/197</f:PeriodKey>
<f:Value>40</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2012</f:PeriodDescription>
<f:PeriodKey>key://16/199</f:PeriodKey>
<f:Value>60</f:Value>
</f:EntryDto>
</e:Entries>
<e:LineId>79540</e:LineId>
<e:Unit>Units</e:Unit>
</e:FinancialPlanLineDto>
<!-- Benefit revenue per unit -->
<e:FinancialPlanLineDto>
<e:AccountDescription>Investment
Benefit</e:AccountDescription>
<e:AccountKey>key://2/$Account/11089</e:AccountKey>
<e:AccountParentDescription>Benefit</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09">
<f:LineAttributeDto>
<f:AltStructureKey>key://2/AGR3/
1403</f:AltStructureKey>
<f:AltStrucutureDescription>ADP</f:AltStrucutureDescription>
</f:LineAttributeDto>
<f:LineAttributeDto>
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
5

<f:AltStructureKey>key://2/Cbs1/
11038</f:AltStructureKey>
<f:AltStrucutureDescription>0198
Networking</f:AltStrucutureDescription>
</f:LineAttributeDto>
</e:Attributes>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2012</f:PeriodDescription>
<f:PeriodKey>key://16/197</f:PeriodKey>
<f:Value>100</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2012</f:PeriodDescription>
<f:PeriodKey>key://16/199</f:PeriodKey>
<f:Value>100</f:Value>
</f:EntryDto>
</e:Entries>
<e:LineId>79540</e:LineId>
<e:Unit>Unit Price</e:Unit>
</e:FinancialPlanLineDto>
<!-- Benefit total revenue -->
<e:FinancialPlanLineDto>
<e:AccountDescription>Investment
Benefit</e:AccountDescription>
<e:AccountKey>key://2/$Account/11089</e:AccountKey>
<e:AccountParentDescription>Benefit</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09">
<f:LineAttributeDto>
<f:AltStructureKey>key://2/AGR3/
1403</f:AltStructureKey>
<f:AltStrucutureDescription>ADP</f:AltStrucutureDescription>
</f:LineAttributeDto>
<f:LineAttributeDto>
<f:AltStructureKey>key://2/Cbs1/
11038</f:AltStructureKey>
<f:AltStrucutureDescription>0198
Networking</f:AltStrucutureDescription>
</f:LineAttributeDto>
</e:Attributes>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2012</f:PeriodDescription>
<f:PeriodKey>key://16/197</f:PeriodKey>
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
6

<f:Value>4000</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2012</f:PeriodDescription>
<f:PeriodKey>key://16/199</f:PeriodKey>
<f:Value>6000</f:Value>
</f:EntryDto>
</e:Entries>
<e:LineId>79540</e:LineId>
<e:Unit>Currency</e:Unit>
</e:FinancialPlanLineDto>
<!-- Labor account -->
<!-- Labor number of FTE -->
<e:FinancialPlanLineDto>
<e:AccountDescription>Labor</e:AccountDescription>
<e:AccountKey>key://2/$Account/11086</e:AccountKey>
<e:AccountParentDescription>Account
Structure</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09">
<f:LineAttributeDto>
<f:AltStructureKey>key://2/Cbs1/
11063</f:AltStructureKey>
<f:AltStrucutureDescription>3211
Engineering</f:AltStrucutureDescription>
</f:LineAttributeDto>
<f:LineAttributeDto>
<f:AltStructureKey>key://2/Obs7/
1805</f:AltStructureKey>
<f:AltStrucutureDescription>On-
Shore</f:AltStrucutureDescription>
</f:LineAttributeDto>
</e:Attributes>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2012</f:PeriodDescription>
<f:PeriodKey>key://16/197</f:PeriodKey>
<f:Value>20</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Feb
2012</f:PeriodDescription>
<f:PeriodKey>key://16/198</f:PeriodKey>
<f:Value>15</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2012</f:PeriodDescription>
<f:PeriodKey>key://16/199</f:PeriodKey>
<f:Value>10</f:Value>
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
7

</f:EntryDto>
</e:Entries>
<e:LineId>79541</e:LineId>
<e:Unit>FTE</e:Unit>
</e:FinancialPlanLineDto>
<!-- Labor effort -->
<e:FinancialPlanLineDto>
<e:AccountDescription>Labor</e:AccountDescription>
<e:AccountKey>key://2/$Account/11086</e:AccountKey>
<e:AccountParentDescription>Account
Structure</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09">
<f:LineAttributeDto>
<f:AltStructureKey>key://2/Cbs1/
11063</f:AltStructureKey>
<f:AltStrucutureDescription>3211
Engineering</f:AltStrucutureDescription>
</f:LineAttributeDto>
<f:LineAttributeDto>
<f:AltStructureKey>key://2/Obs7/
1805</f:AltStructureKey>
<f:AltStrucutureDescription>On-
Shore</f:AltStrucutureDescription>
</f:LineAttributeDto>
</e:Attributes>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2012</f:PeriodDescription>
<f:PeriodKey>key://16/197</f:PeriodKey>
<f:Value>3360</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Feb
2012</f:PeriodDescription>
<f:PeriodKey>key://16/198</f:PeriodKey>
<f:Value>2400</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2012</f:PeriodDescription>
<f:PeriodKey>key://16/199</f:PeriodKey>
<f:Value>1840</f:Value>
</f:EntryDto>
</e:Entries>
<e:LineId>79541</e:LineId>
<e:Unit>Hours</e:Unit>
</e:FinancialPlanLineDto>
<!-- Labor total cost -->
<e:FinancialPlanLineDto>
<e:AccountDescription>Labor</e:AccountDescription>
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
8

<e:AccountKey>key://2/$Account/11086</e:AccountKey>
<e:AccountParentDescription>Account
Structure</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09">
<f:LineAttributeDto>
<f:AltStructureKey>key://2/Cbs1/
11063</f:AltStructureKey>
<f:AltStrucutureDescription>3211
Engineering</f:AltStrucutureDescription>
</f:LineAttributeDto>
<f:LineAttributeDto>
<f:AltStructureKey>key://2/Obs7/
1805</f:AltStructureKey>
<f:AltStrucutureDescription>On-
Shore</f:AltStrucutureDescription>
</f:LineAttributeDto>
</e:Attributes>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2012</f:PeriodDescription>
<f:PeriodKey>key://16/197</f:PeriodKey>
<f:Value>336000</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Feb
2012</f:PeriodDescription>
<f:PeriodKey>key://16/198</f:PeriodKey>
<f:Value>240000</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2012</f:PeriodDescription>
<f:PeriodKey>key://16/199</f:PeriodKey>
<f:Value>184000</f:Value>
</f:EntryDto>
</e:Entries>
<e:LineId>79541</e:LineId>
<e:Unit>Currency</e:Unit>
</e:FinancialPlanLineDto>
<!-- Capital account -->
<!-- Capital number of units -->
<e:FinancialPlanLineDto>
<e:AccountDescription>Manufacturing</e:AccountDescription>
<e:AccountKey>key://2/$Account/13607</e:AccountKey>
<e:AccountParentDescription>Capital</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09"/>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
9

<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2012</f:PeriodDescription>
<f:PeriodKey>key://16/197</f:PeriodKey>
<f:Value>10000</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Feb
2012</f:PeriodDescription>
<f:PeriodKey>key://16/198</f:PeriodKey>
<f:Value>10000</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2012</f:PeriodDescription>
<f:PeriodKey>key://16/199</f:PeriodKey>
<f:Value>10000</f:Value>
</f:EntryDto>
</e:Entries>
<e:LineId>79542</e:LineId>
<e:Unit>Units</e:Unit>
</e:FinancialPlanLineDto>
<!-- Capital cost per unit -->
<e:FinancialPlanLineDto>
<e:AccountDescription>Manufacturing</e:AccountDescription>
<e:AccountKey>key://2/$Account/13607</e:AccountKey>
<e:AccountParentDescription>Capital</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09"/>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2012</f:PeriodDescription>
<f:PeriodKey>key://16/197</f:PeriodKey>
<f:Value>100</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Feb
2012</f:PeriodDescription>
<f:PeriodKey>key://16/198</f:PeriodKey>
<f:Value>100</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2012</f:PeriodDescription>
<f:PeriodKey>key://16/199</f:PeriodKey>
<f:Value>100</f:Value>
</f:EntryDto>
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
10

</e:Entries>
<e:LineId>79542</e:LineId>
<e:Unit>Unit Cost</e:Unit>
</e:FinancialPlanLineDto>
<!-- Capital total cost -->
<e:FinancialPlanLineDto>
<e:AccountDescription>Manufacturing</e:AccountDescription>
<e:AccountKey>key://2/$Account/13607</e:AccountKey>
<e:AccountParentDescription>Capital</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09"/>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2012</f:PeriodDescription>
<f:PeriodKey>key://16/197</f:PeriodKey>
<f:Value>1000000</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Feb
2012</f:PeriodDescription>
<f:PeriodKey>key://16/198</f:PeriodKey>
<f:Value>1000000</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2012</f:PeriodDescription>
<f:PeriodKey>key://16/199</f:PeriodKey>
<f:Value>1000000</f:Value>
</f:EntryDto>
</e:Entries>
<e:LineId>79542</e:LineId>
<e:Unit>Currency</e:Unit>
</e:FinancialPlanLineDto>
<!-- Expense account -->
<!-- Expense total cost -->
<e:FinancialPlanLineDto>
<e:AccountDescription>Hardware</e:AccountDescription>
<e:AccountKey>key://2/$Account/11095</e:AccountKey>
<e:AccountParentDescription>Expense</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09"/>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Feb
2012</f:PeriodDescription>
<f:PeriodKey>key://16/198</f:PeriodKey>
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
11

<f:Value>45000</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2012</f:PeriodDescription>
<f:PeriodKey>key://16/199</f:PeriodKey>
<f:Value>65000</f:Value>
</f:EntryDto>
</e:Entries>
<e:LineId>79543</e:LineId>
<e:Unit>Currency</e:Unit>
</e:FinancialPlanLineDto>
</d:Lines>
<d:ModelDescription>JMC's Work Model</d:ModelDescription>
<d:VersionDescription>Actual</d:VersionDescription>
<d:VersionKey>key://14/57</d:VersionKey>
</c:Dto>
<c:LogTransactionId i:nil="true"/>
</b:OpenSuiteStatus>
</a:Successes>
<a:Warnings xmlns:b="http://schemas.planview.com/PlanviewEnterprise/
OpenSuite/OpenSuiteStatus/2010/01/01"/>
</ReadResult>
</ReadResponse>
</s:Body>
</s:Envelope>
Read - Example 2: Read the Financial Plan Updated in Example 2 of SoapUI
Upsert Examples.
•Use key URIs in the EntityKey and V ersionKey fields to identify the financial plan.
Request
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
xmlns:ns="http://schemas.planview.com/PlanviewEnterprise/Services/FinancialPlan2/
2012/09"
xmlns:ns1="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/
FinancialPlanDto/2013/03"
xmlns:ns2="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/
FinancialPlanLineDto/2013/03"
xmlns:ns3="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/
LineAttributeDto/2012/09"
xmlns:ns4="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/EntryDto/
2010/01/01">
<soapenv:Header/>
<soapenv:Body>
<ns:Read>
<ns:dtos>
<ns1:FinancialPlanDto>
<ns1:EntityKey>key://2/$Plan/15410</ns1:EntityKey>
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
12

<ns1:VersionKey>key://14/57</ns1:VersionKey>
</ns1:FinancialPlanDto>
</ns:dtos>
</ns:Read>
</soapenv:Body>
</soapenv:Envelope>
ResponseResponse
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
<s:Body>
<ReadResponse xmlns="http://schemas.planview.com/PlanviewEnterprise/Services/
FinancialPlan2/2012/09">
<ReadResult xmlns:a="http://schemas.planview.com/PlanviewEnterprise/
OpenSuite/OpenSuiteResult/2010/01/01" xmlns:i="http://www.w3.org/2001/XMLSchema-
instance">
<a:Failures xmlns:b="http://schemas.planview.com/PlanviewEnterprise/
OpenSuite/OpenSuiteStatus/2010/01/01"/>
<a:GeneralErrorMessage i:nil="true"/>
<a:Successes xmlns:b="http://schemas.planview.com/PlanviewEnterprise/
OpenSuite/OpenSuiteStatus/2010/01/01">
<b:OpenSuiteStatus i:type="c:FinancialPlanStatus"
xmlns:c="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/
FinancialPlanStatus/2013/01">
<b:Code i:nil="true"/>
<b:ErrorMessage i:nil="true"/>
<b:SourceIndex>0</b:SourceIndex>
<c:Dto xmlns:d="http://schemas.planview.com/PlanviewEnterprise/
OpenSuite/Dtos/FinancialPlanDto/2013/03">
<d:EntityDescription>Project for a Financial Plan -
JMC</d:EntityDescription>
<d:EntityKey>key://2/$Plan/15410</d:EntityKey>
<d:Key>key://12/2898</d:Key>
<d:Lines xmlns:e="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/FinancialPlanLineDto/2013/03">
<!-- Benefit account -->
<!-- Benefit number of units -->
<e:FinancialPlanLineDto>
<e:AccountDescription>Investment
Benefit</e:AccountDescription>
<e:AccountKey>key://2/$Account/11089</e:AccountKey>
<e:AccountParentDescription>Benefit</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09">
<f:LineAttributeDto>
<f:AltStructureKey>key://2/AGR3/
1403</f:AltStructureKey>
<f:AltStrucutureDescription>ADP</f:AltStrucutureDescription>
</f:LineAttributeDto>
<f:LineAttributeDto>
<f:AltStructureKey>key://2/Cbs1/
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
13

11038</f:AltStructureKey>
<f:AltStrucutureDescription>0198
Networking</f:AltStrucutureDescription>
</f:LineAttributeDto>
</e:Attributes>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2012</f:PeriodDescription>
<f:PeriodKey>key://16/197</f:PeriodKey>
<f:Value>50</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2012</f:PeriodDescription>
<f:PeriodKey>key://16/199</f:PeriodKey>
<f:Value>60</f:Value>
</f:EntryDto>
</e:Entries>
<e:LineId>79540</e:LineId>
<e:Unit>Units</e:Unit>
</e:FinancialPlanLineDto>
<!-- Benefit revenue per unit -->
<e:FinancialPlanLineDto>
<e:AccountDescription>Investment
Benefit</e:AccountDescription>
<e:AccountKey>key://2/$Account/11089</e:AccountKey>
<e:AccountParentDescription>Benefit</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09">
<f:LineAttributeDto>
<f:AltStructureKey>key://2/AGR3/
1403</f:AltStructureKey>
<f:AltStrucutureDescription>ADP</f:AltStrucutureDescription>
</f:LineAttributeDto>
<f:LineAttributeDto>
<f:AltStructureKey>key://2/Cbs1/
11038</f:AltStructureKey>
<f:AltStrucutureDescription>0198
Networking</f:AltStrucutureDescription>
</f:LineAttributeDto>
</e:Attributes>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2012</f:PeriodDescription>
<f:PeriodKey>key://16/197</f:PeriodKey>
<f:Value>100</f:Value>
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
14

</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2012</f:PeriodDescription>
<f:PeriodKey>key://16/199</f:PeriodKey>
<f:Value>100</f:Value>
</f:EntryDto>
</e:Entries>
<e:LineId>79540</e:LineId>
<e:Unit>Unit Price</e:Unit>
</e:FinancialPlanLineDto>
<!-- Benefit total revenue -->
<e:FinancialPlanLineDto>
<e:AccountDescription>Investment
Benefit</e:AccountDescription>
<e:AccountKey>key://2/$Account/11089</e:AccountKey>
<e:AccountParentDescription>Benefit</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09">
<f:LineAttributeDto>
<f:AltStructureKey>key://2/AGR3/
1403</f:AltStructureKey>
<f:AltStrucutureDescription>ADP</f:AltStrucutureDescription>
</f:LineAttributeDto>
<f:LineAttributeDto>
<f:AltStructureKey>key://2/Cbs1/
11038</f:AltStructureKey>
<f:AltStrucutureDescription>0198
Networking</f:AltStrucutureDescription>
</f:LineAttributeDto>
</e:Attributes>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2012</f:PeriodDescription>
<f:PeriodKey>key://16/197</f:PeriodKey>
<f:Value>5000</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2012</f:PeriodDescription>
<f:PeriodKey>key://16/199</f:PeriodKey>
<f:Value>6000</f:Value>
</f:EntryDto>
</e:Entries>
<e:LineId>79540</e:LineId>
<e:Unit>Currency</e:Unit>
</e:FinancialPlanLineDto>
<!-- Labor account -->
<!-- Labor number of FTE -->
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
15

<e:FinancialPlanLineDto>
<e:AccountDescription>Labor</e:AccountDescription>
<e:AccountKey>key://2/$Account/11086</e:AccountKey>
<e:AccountParentDescription>Account
Structure</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09">
<f:LineAttributeDto>
<f:AltStructureKey>key://2/Cbs1/
11063</f:AltStructureKey>
<f:AltStrucutureDescription>3211
Engineering</f:AltStrucutureDescription>
</f:LineAttributeDto>
<f:LineAttributeDto>
<f:AltStructureKey>key://2/Obs7/
1805</f:AltStructureKey>
<f:AltStrucutureDescription>On-
Shore</f:AltStrucutureDescription>
</f:LineAttributeDto>
</e:Attributes>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2012</f:PeriodDescription>
<f:PeriodKey>key://16/197</f:PeriodKey>
<f:Value>20</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Feb
2012</f:PeriodDescription>
<f:PeriodKey>key://16/198</f:PeriodKey>
<f:Value>15</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2012</f:PeriodDescription>
<f:PeriodKey>key://16/199</f:PeriodKey>
<f:Value>10</f:Value>
</f:EntryDto>
</e:Entries>
<e:LineId>79541</e:LineId>
<e:Unit>FTE</e:Unit>
</e:FinancialPlanLineDto>
<!-- Labor effort -->
<e:FinancialPlanLineDto>
<e:AccountDescription>Labor</e:AccountDescription>
<e:AccountKey>key://2/$Account/11086</e:AccountKey>
<e:AccountParentDescription>Account
Structure</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09">
<f:LineAttributeDto>
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
16

<f:AltStructureKey>key://2/Cbs1/
11063</f:AltStructureKey>
<f:AltStrucutureDescription>3211
Engineering</f:AltStrucutureDescription>
</f:LineAttributeDto>
<f:LineAttributeDto>
<f:AltStructureKey>key://2/Obs7/
1805</f:AltStructureKey>
<f:AltStrucutureDescription>On-
Shore</f:AltStrucutureDescription>
</f:LineAttributeDto>
</e:Attributes>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2012</f:PeriodDescription>
<f:PeriodKey>key://16/197</f:PeriodKey>
<f:Value>3360</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Feb
2012</f:PeriodDescription>
<f:PeriodKey>key://16/198</f:PeriodKey>
<f:Value>2400</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2012</f:PeriodDescription>
<f:PeriodKey>key://16/199</f:PeriodKey>
<f:Value>1840</f:Value>
</f:EntryDto>
</e:Entries>
<e:LineId>79541</e:LineId>
<e:Unit>Hours</e:Unit>
</e:FinancialPlanLineDto>
<!-- Labor total cost -->
<e:FinancialPlanLineDto>
<e:AccountDescription>Labor</e:AccountDescription>
<e:AccountKey>key://2/$Account/11086</e:AccountKey>
<e:AccountParentDescription>Account
Structure</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09">
<f:LineAttributeDto>
<f:AltStructureKey>key://2/Cbs1/
11063</f:AltStructureKey>
<f:AltStrucutureDescription>3211
Engineering</f:AltStrucutureDescription>
</f:LineAttributeDto>
<f:LineAttributeDto>
<f:AltStructureKey>key://2/Obs7/
1805</f:AltStructureKey>
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
17

<f:AltStrucutureDescription>On-
Shore</f:AltStrucutureDescription>
</f:LineAttributeDto>
</e:Attributes>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2012</f:PeriodDescription>
<f:PeriodKey>key://16/197</f:PeriodKey>
<f:Value>336000</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Feb
2012</f:PeriodDescription>
<f:PeriodKey>key://16/198</f:PeriodKey>
<f:Value>240000</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2012</f:PeriodDescription>
<f:PeriodKey>key://16/199</f:PeriodKey>
<f:Value>184000</f:Value>
</f:EntryDto>
</e:Entries>
<e:LineId>79541</e:LineId>
<e:Unit>Currency</e:Unit>
</e:FinancialPlanLineDto>
<!-- Capital account -->
<!-- Capital number of units -->
<e:FinancialPlanLineDto>
<e:AccountDescription>Manufacturing</e:AccountDescription>
<e:AccountKey>key://2/$Account/13607</e:AccountKey>
<e:AccountParentDescription>Capital</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09"/>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2012</f:PeriodDescription>
<f:PeriodKey>key://16/197</f:PeriodKey>
<f:Value>10000</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Feb
2012</f:PeriodDescription>
<f:PeriodKey>key://16/198</f:PeriodKey>
<f:Value>10000</f:Value>
</f:EntryDto>
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
18

<f:EntryDto>
<f:PeriodDescription>Mar
2012</f:PeriodDescription>
<f:PeriodKey>key://16/199</f:PeriodKey>
<f:Value>10000</f:Value>
</f:EntryDto>
</e:Entries>
<e:LineId>79542</e:LineId>
<e:Unit>Units</e:Unit>
</e:FinancialPlanLineDto>
<!-- Capital cost per unit -->
<e:FinancialPlanLineDto>
<e:AccountDescription>Manufacturing</e:AccountDescription>
<e:AccountKey>key://2/$Account/13607</e:AccountKey>
<e:AccountParentDescription>Capital</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09"/>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2012</f:PeriodDescription>
<f:PeriodKey>key://16/197</f:PeriodKey>
<f:Value>100</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Feb
2012</f:PeriodDescription>
<f:PeriodKey>key://16/198</f:PeriodKey>
<f:Value>100</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2012</f:PeriodDescription>
<f:PeriodKey>key://16/199</f:PeriodKey>
<f:Value>100</f:Value>
</f:EntryDto>
</e:Entries>
<e:LineId>79542</e:LineId>
<e:Unit>Unit Cost</e:Unit>
</e:FinancialPlanLineDto>
<!-- Capital total cost -->
<e:FinancialPlanLineDto>
<e:AccountDescription>Manufacturing</e:AccountDescription>
<e:AccountKey>key://2/$Account/13607</e:AccountKey>
<e:AccountParentDescription>Capital</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09"/>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
19

<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2012</f:PeriodDescription>
<f:PeriodKey>key://16/197</f:PeriodKey>
<f:Value>1000000</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Feb
2012</f:PeriodDescription>
<f:PeriodKey>key://16/198</f:PeriodKey>
<f:Value>1000000</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2012</f:PeriodDescription>
<f:PeriodKey>key://16/199</f:PeriodKey>
<f:Value>1000000</f:Value>
</f:EntryDto>
</e:Entries>
<e:LineId>79542</e:LineId>
<e:Unit>Currency</e:Unit>
</e:FinancialPlanLineDto>
<!-- Expense account -->
<!-- Expense total cost -->
<e:FinancialPlanLineDto>
<e:AccountDescription>Hardware</e:AccountDescription>
<e:AccountKey>key://2/$Account/11095</e:AccountKey>
<e:AccountParentDescription>Expense</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09"/>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Feb
2012</f:PeriodDescription>
<f:PeriodKey>key://16/198</f:PeriodKey>
<f:Value>45000</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2012</f:PeriodDescription>
<f:PeriodKey>key://16/199</f:PeriodKey>
<f:Value>65000</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Apr
2012</f:PeriodDescription>
<f:PeriodKey>key://16/200</f:PeriodKey>
<f:Value>75000</f:Value>
</f:EntryDto>
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
20

</e:Entries>
<e:LineId>79543</e:LineId>
<e:Unit>Currency</e:Unit>
</e:FinancialPlanLineDto>
</d:Lines>
<d:ModelDescription>JMC's Work Model</d:ModelDescription>
<d:VersionDescription>Actual</d:VersionDescription>
<d:VersionKey>key://14/57</d:VersionKey>
</c:Dto>
<c:LogTransactionId i:nil="true"/>
</b:OpenSuiteStatus>
</a:Successes>
<a:Warnings xmlns:b="http://schemas.planview.com/PlanviewEnterprise/
OpenSuite/OpenSuiteStatus/2010/01/01"/>
</ReadResult>
</ReadResponse>
</s:Body>
</s:Envelope>
Read – Example 3: Read the Financial Plan in Example 3 of SoapUI Upsert
Examples, Which Clears Editable Fields in a Specified Period Range
•Read the r esults fr om Upsert Example 3 which r emoves all editable fields fr om January 2012 to Mar ch 2012 for all
account types except ACTP$LAB and ACTP$CAP (Labor and Capital).
•A key URI in the Key field was used to identify the financial plan.
Request
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
xmlns:ns="http://schemas.planview.com/PlanviewEnterprise/Services/FinancialPlan2/
2012/09" xmlns:ns1="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/
FinancialPlanDto/2013/03" xmlns:ns2="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/FinancialPlanLineDto/2013/03"
xmlns:ns3="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/
LineAttributeDto/2012/09" xmlns:ns4="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<soapenv:Header/>
<soapenv:Body>
<ns:Read>
<ns:dtos>
<ns1:FinancialPlanDto>
<ns1:Key>key://12/2898</ns1:Key>
</ns1:FinancialPlanDto>
</ns:dtos>
</ns:Read>
</soapenv:Body>
</soapenv:Envelope>
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
21

ResponseResponse
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
<s:Body>
<ReadResponse xmlns="http://schemas.planview.com/PlanviewEnterprise/Services/
FinancialPlan2/2012/09">
<ReadResult xmlns:a="http://schemas.planview.com/PlanviewEnterprise/
OpenSuite/OpenSuiteResult/2010/01/01" xmlns:i="http://www.w3.org/2001/XMLSchema-
instance">
<a:Failures xmlns:b="http://schemas.planview.com/PlanviewEnterprise/
OpenSuite/OpenSuiteStatus/2010/01/01"/>
<a:GeneralErrorMessage i:nil="true"/>
<a:Successes xmlns:b="http://schemas.planview.com/PlanviewEnterprise/
OpenSuite/OpenSuiteStatus/2010/01/01">
<b:OpenSuiteStatus i:type="c:FinancialPlanStatus"
xmlns:c="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/
FinancialPlanStatus/2013/01">
<b:Code i:nil="true"/>
<b:ErrorMessage i:nil="true"/>
<b:SourceIndex>0</b:SourceIndex>
<c:Dto xmlns:d="http://schemas.planview.com/PlanviewEnterprise/
OpenSuite/Dtos/FinancialPlanDto/2013/03">
<d:EntityDescription>Project for a Financial Plan -
JMC</d:EntityDescription>
<d:EntityKey>key://2/$Plan/15410</d:EntityKey>
<d:Key>key://12/2898</d:Key>
<d:Lines xmlns:e="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/FinancialPlanLineDto/2013/03">
<!-- Benefit account -->
<!-- Benefit number of units -->
<e:FinancialPlanLineDto>
<e:AccountDescription>Investment
Benefit</e:AccountDescription>
<e:AccountKey>key://2/$Account/11089</e:AccountKey>
<e:AccountParentDescription>Benefit</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09">
<f:LineAttributeDto>
<f:AltStructureKey>key://2/AGR3/
1403</f:AltStructureKey>
<f:AltStrucutureDescription>ADP</f:AltStrucutureDescription>
</f:LineAttributeDto>
<f:LineAttributeDto>
<f:AltStructureKey>key://2/Cbs1/
11038</f:AltStructureKey>
<f:AltStrucutureDescription>0198
Networking</f:AltStrucutureDescription>
</f:LineAttributeDto>
</e:Attributes>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
22

PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01"/>
<e:LineId>79540</e:LineId>
<e:Unit>Units</e:Unit>
</e:FinancialPlanLineDto>
<!-- Benefit revenue per unit -->
<e:FinancialPlanLineDto>
<e:AccountDescription>Investment
Benefit</e:AccountDescription>
<e:AccountKey>key://2/$Account/11089</e:AccountKey>
<e:AccountParentDescription>Benefit</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09">
<f:LineAttributeDto>
<f:AltStructureKey>key://2/AGR3/
1403</f:AltStructureKey>
<f:AltStrucutureDescription>ADP</f:AltStrucutureDescription>
</f:LineAttributeDto>
<f:LineAttributeDto>
<f:AltStructureKey>key://2/Cbs1/
11038</f:AltStructureKey>
<f:AltStrucutureDescription>0198
Networking</f:AltStrucutureDescription>
</f:LineAttributeDto>
</e:Attributes>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01"/>
<e:LineId>79540</e:LineId>
<e:Unit>Unit Price</e:Unit>
</e:FinancialPlanLineDto>
<!-- Benefit total revenue -->
<e:FinancialPlanLineDto>
<e:AccountDescription>Investment
Benefit</e:AccountDescription>
<e:AccountKey>key://2/$Account/11089</e:AccountKey>
<e:AccountParentDescription>Benefit</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09">
<f:LineAttributeDto>
<f:AltStructureKey>key://2/AGR3/
1403</f:AltStructureKey>
<f:AltStrucutureDescription>ADP</f:AltStrucutureDescription>
</f:LineAttributeDto>
<f:LineAttributeDto>
<f:AltStructureKey>key://2/Cbs1/
11038</f:AltStructureKey>
<f:AltStrucutureDescription>0198
Networking</f:AltStrucutureDescription>
</f:LineAttributeDto>
</e:Attributes>
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
23

<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01"/>
<e:LineId>79540</e:LineId>
<e:Unit>Currency</e:Unit>
</e:FinancialPlanLineDto>
<!-- Labor account -->
<!-- Labor number of FTE -->
<e:FinancialPlanLineDto>
<e:AccountDescription>Labor</e:AccountDescription>
<e:AccountKey>key://2/$Account/11086</e:AccountKey>
<e:AccountParentDescription>Account
Structure</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09">
<f:LineAttributeDto>
<f:AltStructureKey>key://2/Cbs1/
11063</f:AltStructureKey>
<f:AltStrucutureDescription>3211
Engineering</f:AltStrucutureDescription>
</f:LineAttributeDto>
<f:LineAttributeDto>
<f:AltStructureKey>key://2/Obs7/
1805</f:AltStructureKey>
<f:AltStrucutureDescription>On-
Shore</f:AltStrucutureDescription>
</f:LineAttributeDto>
</e:Attributes>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2012</f:PeriodDescription>
<f:PeriodKey>key://16/197</f:PeriodKey>
<f:Value>20</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Feb
2012</f:PeriodDescription>
<f:PeriodKey>key://16/198</f:PeriodKey>
<f:Value>15</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2012</f:PeriodDescription>
<f:PeriodKey>key://16/199</f:PeriodKey>
<f:Value>10</f:Value>
</f:EntryDto>
</e:Entries>
<e:LineId>79541</e:LineId>
<e:Unit>FTE</e:Unit>
</e:FinancialPlanLineDto>
<!-- Labor effort -->
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
24

<e:FinancialPlanLineDto>
<e:AccountDescription>Labor</e:AccountDescription>
<e:AccountKey>key://2/$Account/11086</e:AccountKey>
<e:AccountParentDescription>Account
Structure</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09">
<f:LineAttributeDto>
<f:AltStructureKey>key://2/Cbs1/
11063</f:AltStructureKey>
<f:AltStrucutureDescription>3211
Engineering</f:AltStrucutureDescription>
</f:LineAttributeDto>
<f:LineAttributeDto>
<f:AltStructureKey>key://2/Obs7/
1805</f:AltStructureKey>
<f:AltStrucutureDescription>On-
Shore</f:AltStrucutureDescription>
</f:LineAttributeDto>
</e:Attributes>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2012</f:PeriodDescription>
<f:PeriodKey>key://16/197</f:PeriodKey>
<f:Value>3360</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Feb
2012</f:PeriodDescription>
<f:PeriodKey>key://16/198</f:PeriodKey>
<f:Value>2400</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2012</f:PeriodDescription>
<f:PeriodKey>key://16/199</f:PeriodKey>
<f:Value>1840</f:Value>
</f:EntryDto>
</e:Entries>
<e:LineId>79541</e:LineId>
<e:Unit>Hours</e:Unit>
</e:FinancialPlanLineDto>
<!-- Labor total cost -->
<e:FinancialPlanLineDto>
<e:AccountDescription>Labor</e:AccountDescription>
<e:AccountKey>key://2/$Account/11086</e:AccountKey>
<e:AccountParentDescription>Account
Structure</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09">
<f:LineAttributeDto>
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
25

<f:AltStructureKey>key://2/Cbs1/
11063</f:AltStructureKey>
<f:AltStrucutureDescription>3211
Engineering</f:AltStrucutureDescription>
</f:LineAttributeDto>
<f:LineAttributeDto>
<f:AltStructureKey>key://2/Obs7/
1805</f:AltStructureKey>
<f:AltStrucutureDescription>On-
Shore</f:AltStrucutureDescription>
</f:LineAttributeDto>
</e:Attributes>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2012</f:PeriodDescription>
<f:PeriodKey>key://16/197</f:PeriodKey>
<f:Value>336000</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Feb
2012</f:PeriodDescription>
<f:PeriodKey>key://16/198</f:PeriodKey>
<f:Value>240000</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2012</f:PeriodDescription>
<f:PeriodKey>key://16/199</f:PeriodKey>
<f:Value>184000</f:Value>
</f:EntryDto>
</e:Entries>
<e:LineId>79541</e:LineId>
<e:Unit>Currency</e:Unit>
</e:FinancialPlanLineDto>
<!-- Capital account -->
<!-- Capital number of units -->
<e:FinancialPlanLineDto>
<e:AccountDescription>Manufacturing</e:AccountDescription>
<e:AccountKey>key://2/$Account/13607</e:AccountKey>
<e:AccountParentDescription>Capital</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09"/>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2012</f:PeriodDescription>
<f:PeriodKey>key://16/197</f:PeriodKey>
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
26

<f:Value>10000</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Feb
2012</f:PeriodDescription>
<f:PeriodKey>key://16/198</f:PeriodKey>
<f:Value>10000</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2012</f:PeriodDescription>
<f:PeriodKey>key://16/199</f:PeriodKey>
<f:Value>10000</f:Value>
</f:EntryDto>
</e:Entries>
<e:LineId>79542</e:LineId>
<e:Unit>Units</e:Unit>
</e:FinancialPlanLineDto>
<!-- Capital cost per unit -->
<e:FinancialPlanLineDto>
<e:AccountDescription>Manufacturing</e:AccountDescription>
<e:AccountKey>key://2/$Account/13607</e:AccountKey>
<e:AccountParentDescription>Capital</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09"/>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2012</f:PeriodDescription>
<f:PeriodKey>key://16/197</f:PeriodKey>
<f:Value>100</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Feb
2012</f:PeriodDescription>
<f:PeriodKey>key://16/198</f:PeriodKey>
<f:Value>100</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2012</f:PeriodDescription>
<f:PeriodKey>key://16/199</f:PeriodKey>
<f:Value>100</f:Value>
</f:EntryDto>
</e:Entries>
<e:LineId>79542</e:LineId>
<e:Unit>Unit Cost</e:Unit>
</e:FinancialPlanLineDto>
<!-- Capital total cost -->
<e:FinancialPlanLineDto>
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
27

<e:AccountDescription>Manufacturing</e:AccountDescription>
<e:AccountKey>key://2/$Account/13607</e:AccountKey>
<e:AccountParentDescription>Capital</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09"/>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2012</f:PeriodDescription>
<f:PeriodKey>key://16/197</f:PeriodKey>
<f:Value>1000000</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Feb
2012</f:PeriodDescription>
<f:PeriodKey>key://16/198</f:PeriodKey>
<f:Value>1000000</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2012</f:PeriodDescription>
<f:PeriodKey>key://16/199</f:PeriodKey>
<f:Value>1000000</f:Value>
</f:EntryDto>
</e:Entries>
<e:LineId>79542</e:LineId>
<e:Unit>Currency</e:Unit>
</e:FinancialPlanLineDto>
<!-- Expense account -->
<!-- Expense total cost -->
<e:FinancialPlanLineDto>
<e:AccountDescription>Hardware</e:AccountDescription>
<e:AccountKey>key://2/$Account/11095</e:AccountKey>
<e:AccountParentDescription>Expense</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09"/>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Apr
2012</f:PeriodDescription>
<f:PeriodKey>key://16/200</f:PeriodKey>
<f:Value>75000</f:Value>
</f:EntryDto>
</e:Entries>
<e:LineId>79543</e:LineId>
<e:Unit>Currency</e:Unit>
</e:FinancialPlanLineDto>
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
28

</d:Lines>
<d:ModelDescription>JMC's Work Model</d:ModelDescription>
<d:VersionDescription>Actual</d:VersionDescription>
<d:VersionKey>key://14/57</d:VersionKey>
</c:Dto>
<c:LogTransactionId i:nil="true"/>
</b:OpenSuiteStatus>
</a:Successes>
<a:Warnings xmlns:b="http://schemas.planview.com/PlanviewEnterprise/
OpenSuite/OpenSuiteStatus/2010/01/01"/>
</ReadResult>
</ReadResponse>
</s:Body>
</s:Envelope>
SoapUI Upsert Examples
Upsert – Example 1: Cr eate a financial plan
•This example cr eates a work financial plan utilizing accounts for income, outgo, and labor .
Request
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
xmlns:ns="http://schemas.planview.com/PlanviewEnterprise/Services/FinancialPlan2/
2012/09"
xmlns:ns1="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/
FinancialPlanDto/2013/03"
xmlns:ns2="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/
FinancialPlanLineDto/2013/03"
xmlns:ns3="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/
LineAttributeDto/2012/09"
xmlns:ns4="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/EntryDto/
2010/01/01"
xmlns:ns5="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/
DeleteEditableFinancialPlanEntriesDto/2013/03"
xmlns:arr="http://schemas.microsoft.com/2003/10/Serialization/Arrays">
<soapenv:Header/>
<soapenv:Body>
<ns:Upsert>
<ns:dtos>
<ns1:FinancialPlanDto>
<ns1:EntityKey>key://2/$Plan/15410</ns1:EntityKey>
<ns1:Key>ekey://12/MyFinancialPlan/
WorkPlan1</ns1:Key>
<ns1:Lines>
<!-- Add a Benefit account. Provide the number of units and per
unit price. -->
<!-- Benefit number of units -->
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
29

<ns2:FinancialPlanLineDto>
<ns2:AccountKey>key://2/$Account/11089</ns2:AccountKey>
<ns2:Attributes>
<ns3:LineAttributeDto>
<ns3:AltStructureKey>key://2/AGR3/
1403</ns3:AltStructureKey>
</ns3:LineAttributeDto>
<ns3:LineAttributeDto>
<ns3:AltStructureKey>key://2/Cbs1/
11038</ns3:AltStructureKey>
</ns3:LineAttributeDto>
</ns2:Attributes>
<ns2:CurrencyKey>key://1/USD</ns2:CurrencyKey>
<ns2:Entries>
<ns4:EntryDto>
<ns4:PeriodKey>key://16/197</ns4:PeriodKey>
<ns4:Value>40</ns4:Value>
</ns4:EntryDto>
<ns4:EntryDto>
<ns4:PeriodKey>key://16/199</ns4:PeriodKey>
<ns4:Value>60</ns4:Value>
</ns4:EntryDto>
</ns2:Entries>
<ns2:Unit>Units</ns2:Unit>
</ns2:FinancialPlanLineDto>
<!-- Benefit unit price -->
<ns2:FinancialPlanLineDto>
<ns2:AccountKey>key://2/$Account/11089</ns2:AccountKey>
<ns2:Attributes>
<ns3:LineAttributeDto>
<ns3:AltStructureKey>key://2/AGR3/
1403</ns3:AltStructureKey>
</ns3:LineAttributeDto>
<ns3:LineAttributeDto>
<ns3:AltStructureKey>key://2/Cbs1/
11038</ns3:AltStructureKey>
</ns3:LineAttributeDto>
</ns2:Attributes>
<ns2:CurrencyKey>key://1/USD</ns2:CurrencyKey>
<ns2:Entries>
<ns4:EntryDto>
<ns4:PeriodKey>key://16/197</ns4:PeriodKey>
<ns4:Value>100</ns4:Value>
</ns4:EntryDto>
<ns4:EntryDto>
<ns4:PeriodKey>key://16/199</ns4:PeriodKey>
<ns4:Value>100</ns4:Value>
</ns4:EntryDto>
</ns2:Entries>
<ns2:Unit>Unit Price</ns2:Unit>
</ns2:FinancialPlanLineDto>
<!-- Add a Labor account. Provide the number FTE. -->
<ns2:FinancialPlanLineDto>
<ns2:AccountKey>key://2/$Account/11086</ns2:AccountKey>
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
30

<ns2:Attributes>
<ns3:LineAttributeDto>
<ns3:AltStructureKey>key://2/Cbs1/
11063</ns3:AltStructureKey>
</ns3:LineAttributeDto>
<ns3:LineAttributeDto>
<ns3:AltStructureKey>key://2/Obs7/
1805</ns3:AltStructureKey>
</ns3:LineAttributeDto>
</ns2:Attributes>
<ns2:CurrencyKey>key://1/USD</ns2:CurrencyKey>
<ns2:Entries>
<ns4:EntryDto>
<ns4:PeriodKey>key://16/197</ns4:PeriodKey>
<ns4:Value>20</ns4:Value>
</ns4:EntryDto>
<ns4:EntryDto>
<ns4:PeriodKey>key://16/198</ns4:PeriodKey>
<ns4:Value>15</ns4:Value>
</ns4:EntryDto>
<ns4:EntryDto>
<ns4:PeriodKey>key://16/199</ns4:PeriodKey>
<ns4:Value>10</ns4:Value>
</ns4:EntryDto>
</ns2:Entries>
<ns2:Unit>FTE</ns2:Unit>
</ns2:FinancialPlanLineDto>
<!-- Add a Capital account. Provide the number of units and
units cost -->
<!-- Capital number of units -->
<ns2:FinancialPlanLineDto>
<ns2:AccountKey>key://2/$Account/13607</ns2:AccountKey>
<ns2:CurrencyKey>key://1/USD</ns2:CurrencyKey>
<ns2:Entries>
<ns4:EntryDto>
<ns4:PeriodKey>key://16/197</ns4:PeriodKey>
<ns4:Value>10000</ns4:Value>
</ns4:EntryDto>
<ns4:EntryDto>
<ns4:PeriodKey>key://16/198</ns4:PeriodKey>
<ns4:Value>10000</ns4:Value>
</ns4:EntryDto>
<ns4:EntryDto>
<ns4:PeriodKey>key://16/199</ns4:PeriodKey>
<ns4:Value>10000</ns4:Value>
</ns4:EntryDto>
</ns2:Entries>
<ns2:Unit>Units</ns2:Unit>
</ns2:FinancialPlanLineDto>
<!-- Capital unit cost -->
<ns2:FinancialPlanLineDto>
<ns2:AccountKey>key://2/$Account/13607</ns2:AccountKey>
<ns2:CurrencyKey>key://1/USD</ns2:CurrencyKey>
<ns2:Entries>
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
31

<ns4:EntryDto>
<ns4:PeriodKey>key://16/197</ns4:PeriodKey>
<ns4:Value>100</ns4:Value>
</ns4:EntryDto>
<ns4:EntryDto>
<ns4:PeriodKey>key://16/198</ns4:PeriodKey>
<ns4:Value>100</ns4:Value>
</ns4:EntryDto>
<ns4:EntryDto>
<ns4:PeriodKey>key://16/199</ns4:PeriodKey>
<ns4:Value>100</ns4:Value>
</ns4:EntryDto>
</ns2:Entries>
<ns2:Unit>Unit Cost</ns2:Unit>
</ns2:FinancialPlanLineDto>
<!-- Add an Expense account. Provide the total cost in USD. -->
<ns2:FinancialPlanLineDto>
<ns2:AccountKey>key://2/$Account/11095</ns2:AccountKey>
<ns2:CurrencyKey>key://1/USD</ns2:CurrencyKey>
<ns2:Entries>
<ns4:EntryDto>
<ns4:PeriodKey>key://16/198</ns4:PeriodKey>
<ns4:Value>45000</ns4:Value>
</ns4:EntryDto>
<ns4:EntryDto>
<ns4:PeriodKey>key://16/199</ns4:PeriodKey>
<ns4:Value>65000</ns4:Value>
</ns4:EntryDto>
</ns2:Entries>
<ns2:Unit>Currency</ns2:Unit>
</ns2:FinancialPlanLineDto>
</ns1:Lines>
<ns1:VersionKey>key://14/57</ns1:VersionKey>
</ns1:FinancialPlanDto>
</ns:dtos>
</ns:Upsert>
</soapenv:Body>
</soapenv:Envelope>
Upsert – Example 2: Update a Financial Plan
•Update the financial plan cr eated in Example 1.
•We do not have to put the entir e plan in the r equest. The following r equest incr eases the number of Benefit units in
January 2012 (period 197) from 40 to 50 and to adds an entir ely new Expenses in April 2012 (period 200).
Request
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
32

xmlns:ns="http://schemas.planview.com/PlanviewEnterprise/Services/FinancialPlan2/
2012/09"
xmlns:ns1="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/
FinancialPlanDto/2013/03"
xmlns:ns2="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/
FinancialPlanLineDto/2013/03"
xmlns:ns3="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/
LineAttributeDto/2012/09" x
mlns:ns4="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/EntryDto/
2010/01/01"
xmlns:ns5="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/
DeleteEditableFinancialPlanEntriesDto/2013/03"
xmlns:arr="http://schemas.microsoft.com/2003/10/Serialization/Arrays">
<soapenv:Header/>
<soapenv:Body>
<ns:Upsert>
<ns:dtos>
<ns1:FinancialPlanDto>
<ns1:Key>ekey://12/MyFinancialPlan/WorkPlan1</ns1:Key>
<ns1:Lines>
<!-- Benefit number of units -->
<ns2:FinancialPlanLineDto>
<ns2:AccountKey>key://2/$Account/11089</ns2:AccountKey>
<ns2:Attributes>
<ns3:LineAttributeDto>
<ns3:AltStructureKey>key://2/AGR3/
1403</ns3:AltStructureKey>
</ns3:LineAttributeDto>
<ns3:LineAttributeDto>
<ns3:AltStructureKey>key://2/Cbs1/
11038</ns3:AltStructureKey>
</ns3:LineAttributeDto>
</ns2:Attributes>
<ns2:CurrencyKey>key://1/USD</ns2:CurrencyKey>
<ns2:Entries>
<ns4:EntryDto>
<ns4:PeriodKey>key://16/197</ns4:PeriodKey>
<ns4:Value>50</ns4:Value>
</ns4:EntryDto>
</ns2:Entries>
<ns2:Unit>Units</ns2:Unit>
</ns2:FinancialPlanLineDto>
<!-- Expense total cost-->
<ns2:FinancialPlanLineDto>
<ns2:AccountKey>key://2/$Account/11095</ns2:AccountKey>
<ns2:CurrencyKey>key://1/USD</ns2:CurrencyKey>
<ns2:Entries>
<ns4:EntryDto>
<ns4:PeriodKey>key://16/200</ns4:PeriodKey>
<ns4:Value>75000</ns4:Value>
</ns4:EntryDto>
</ns2:Entries>
<ns2:Unit>Currency</ns2:Unit>
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
33

</ns2:FinancialPlanLineDto>
</ns1:Lines>
</ns1:FinancialPlanDto>
</ns:dtos>
</ns:Upsert>
</soapenv:Body>
</soapenv:Envelope>
Upsert –Example 3: Clear Editable Fields in Period Range
•Using the r esults fr om Example 2 above, clear the editable fields in the period range 197 to 199.
•Skip all fields for account types ACTP$LAB and ACTP$EXP .
Request
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
xmlns:ns="http://schemas.planview.com/PlanviewEnterprise/Services/FinancialPlan2/
2012/09"
xmlns:ns1="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/
FinancialPlanDto/2013/03"
xmlns:ns2="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/
FinancialPlanLineDto/2013/03"
xmlns:ns3="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/
LineAttributeDto/2012/09"
xmlns:ns4="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/EntryDto/
2010/01/01"
xmlns:ns5="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/
DeleteEditableFinancialPlanEntriesDto/2013/03"
xmlns:arr="http://schemas.microsoft.com/2003/10/Serialization/Arrays">
<soapenv:Header/>
<soapenv:Body>
<ns:Upsert>
<ns:dtos>
<ns1:FinancialPlanDto>
<ns1:Key>ekey://12/MyFinancialPlan/WorkPlan1</ns1:Key>
</ns1:FinancialPlanDto>
</ns:dtos>
<ns:deleteEditableFinancialPlanEntriesDto>
<ns5:AccountTypesToPreserveKeys>
<arr:string>key://2/AcctType/ACTP$LAB</arr:string>
<arr:string>key://2/AcctType/ACTP$CAP</arr:string>
</ns5:AccountTypesToPreserveKeys>
<ns5:FinalPeriodKey>key://16/199</ns5:FinalPeriodKey>
<ns5:FirstPeriodKey>key://16/197</ns5:FirstPeriodKey>
</ns:deleteEditableFinancialPlanEntriesDto>
</ns:Upsert>
</soapenv:Body>
</soapenv:Envelope>
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
34

ResponseResponse
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
<s:Body>
<UpsertResponse xmlns="http://schemas.planview.com/PlanviewEnterprise/
Services/FinancialPlan2/2012/09">
<UpsertResult xmlns:a="http://schemas.planview.com/PlanviewEnterprise/
OpenSuite/OpenSuiteResult/2010/01/01" xmlns:i="http://www.w3.org/2001/XMLSchema-
instance">
<a:Failures xmlns:b="http://schemas.planview.com/PlanviewEnterprise/
OpenSuite/OpenSuiteStatus/2010/01/01"/>
<a:GeneralErrorMessage i:nil="true"/>
<a:Successes xmlns:b="http://schemas.planview.com/PlanviewEnterprise/
OpenSuite/OpenSuiteStatus/2010/01/01">
<b:OpenSuiteStatus i:type="c:FinancialPlanStatus"
xmlns:c="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/
FinancialPlanStatus/2013/01">
<b:Code i:nil="true"/>
<b:ErrorMessage i:nil="true"/>
<b:SourceIndex>0</b:SourceIndex>
<c:Dto xmlns:d="http://schemas.planview.com/PlanviewEnterprise/
OpenSuite/Dtos/FinancialPlanDto/2013/03">
<d:EntityDescription i:nil="true"/>
<d:EntityKey i:nil="true"/>
<d:Key>key://12/2898</d:Key>
<d:Lines i:nil="true" xmlns:e="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/FinancialPlanLineDto/2013/03"/>
<d:ModelDescription i:nil="true"/>
<d:VersionDescription i:nil="true"/>
<d:VersionKey i:nil="true"/>
</c:Dto>
<c:LogTransactionId>4517</c:LogTransactionId>
</b:OpenSuiteStatus>
</a:Successes>
<a:Warnings xmlns:b="http://schemas.planview.com/PlanviewEnterprise/
OpenSuite/OpenSuiteStatus/2010/01/01"/>
</UpsertResult>
</UpsertResponse>
</s:Body>
</s:Envelope>
SoapUI Read Examples
Read – Example 1: Read the Financial Plan Cr eated in Example 1 of SoapUI
Upsert Examples.
•Use the an eKey URI in the Key field to identify the financial plan.
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
35

Request
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
xmlns:ns="http://schemas.planview.com/PlanviewEnterprise/Services/FinancialPlan2/
2012/09"
xmlns:ns1="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/
FinancialPlanDto/2013/03"
xmlns:ns2="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/
FinancialPlanLineDto/2013/03"
xmlns:ns3="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/
LineAttributeDto/2012/09"
xmlns:ns4="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/EntryDto/
2010/01/01">
<soapenv:Header/>
<soapenv:Body>
<ns:Read>
<ns:dtos>
<ns1:FinancialPlanDto>
<ns1:Key>ekey://12/Documentation/Financial_Plan</ns1:Key>
</ns1:FinancialPlanDto>
</ns:dtos>
</ns:Read>
</soapenv:Body>
</soapenv:Envelope
ResponseResponse
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
<s:Body>
<ReadResponse xmlns="http://schemas.planview.com/PlanviewEnterprise/Services/
FinancialPlan2/2012/09">
<ReadResult xmlns:a="http://schemas.planview.com/PlanviewEnterprise/
OpenSuite/OpenSuiteResult/2010/01/01"
xmlns:i="http://www.w3.org/2001/XMLSchema-instance">
<a:Failures xmlns:b="http://schemas.planview.com/PlanviewEnterprise/
OpenSuite/OpenSuiteStatus/2010/01/01"/>
<a:GeneralErrorMessage i:nil="true"/>
<a:Successes xmlns:b="http://schemas.planview.com/PlanviewEnterprise/
OpenSuite/OpenSuiteStatus/2010/01/01">
<b:OpenSuiteStatus i:type="c:FinancialPlanStatus"
xmlns:c="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/
FinancialPlanStatus/2013/01">
<b:Code i:nil="true"/>
<b:ErrorMessage i:nil="true"/>
<b:SourceIndex>0</b:SourceIndex>
<c:Dto xmlns:d="http://schemas.planview.com/PlanviewEnterprise/
OpenSuite/Dtos/FinancialPlanDto/2013/03">
<d:EntityDescription>Documentation: Project for Financial
Plan</d:EntityDescription>
<d:EntityKey>key://2/$Plan/19138</d:EntityKey>
<d:Key>key://12/2942</d:Key>
<d:Lines xmlns:e="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/FinancialPlanLineDto/2013/03">
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
36

<e:FinancialPlanLineDto>
<e:AccountDescription>Revenue</e:AccountDescription>
<e:AccountKey>key://2/$Account/11090</e:AccountKey>
<e:AccountParentDescription>Benefit</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09">
<f:LineAttributeDto>
<f:AltStructureKey>key://2/AGR3/
1403</f:AltStructureKey>
<f:AltStrucutureDescription>ADP</f:AltStrucutureDescription>
</f:LineAttributeDto>
<f:LineAttributeDto>
<f:AltStructureKey>key://2/Cbs1/
11038</f:AltStructureKey>
<f:AltStrucutureDescription>0198
Networking</f:AltStrucutureDescription>
</f:LineAttributeDto>
</e:Attributes>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2020</f:PeriodDescription>
<f:PeriodKey>key://16/293</f:PeriodKey>
<f:Value>10000</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2020</f:PeriodDescription>
<f:PeriodKey>key://16/295</f:PeriodKey>
<f:Value>12000</f:Value>
</f:EntryDto>
</e:Entries>
<e:LineId>79642</e:LineId>
<e:Note>Line Note for Account:Benefit/Revenue</e:Note>
<e:Unit>Units</e:Unit>
</e:FinancialPlanLineDto>
<e:FinancialPlanLineDto>
<e:AccountDescription>Revenue</e:AccountDescription>
<e:AccountKey>key://2/$Account/11090</e:AccountKey>
<e:AccountParentDescription>Benefit</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09">
<f:LineAttributeDto>
<f:AltStructureKey>key://2/AGR3/
1403</f:AltStructureKey>
<f:AltStrucutureDescription>ADP</f:AltStrucutureDescription>
</f:LineAttributeDto>
<f:LineAttributeDto>
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
37

<f:AltStructureKey>key://2/Cbs1/
11038</f:AltStructureKey>
<f:AltStrucutureDescription>0198
Networking</f:AltStrucutureDescription>
</f:LineAttributeDto>
</e:Attributes>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2020</f:PeriodDescription>
<f:PeriodKey>key://16/293</f:PeriodKey>
<f:Value>50</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2020</f:PeriodDescription>
<f:PeriodKey>key://16/295</f:PeriodKey>
<f:Value>60</f:Value>
</f:EntryDto>
</e:Entries>
<e:LineId>79642</e:LineId>
<e:Note>Line Note for Account:Benefit/Revenue</e:Note>
<e:Unit>Unit Price</e:Unit>
</e:FinancialPlanLineDto>
<e:FinancialPlanLineDto>
<e:AccountDescription>Revenue</e:AccountDescription>
<e:AccountKey>key://2/$Account/11090</e:AccountKey>
<e:AccountParentDescription>Benefit</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09">
<f:LineAttributeDto>
<f:AltStructureKey>key://2/AGR3/
1403</f:AltStructureKey>
<f:AltStrucutureDescription>ADP</f:AltStrucutureDescription>
</f:LineAttributeDto>
<f:LineAttributeDto>
<f:AltStructureKey>key://2/Cbs1/
11038</f:AltStructureKey>
<f:AltStrucutureDescription>0198
Networking</f:AltStrucutureDescription>
</f:LineAttributeDto>
</e:Attributes>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2020</f:PeriodDescription>
<f:PeriodKey>key://16/293</f:PeriodKey>
<f:Value>500000</f:Value>
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
38

</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2020</f:PeriodDescription>
<f:PeriodKey>key://16/295</f:PeriodKey>
<f:Value>720000</f:Value>
</f:EntryDto>
</e:Entries>
<e:LineId>79642</e:LineId>
<e:Note>Line Note for Account:Benefit/Revenue</e:Note>
<e:Unit>Currency</e:Unit>
</e:FinancialPlanLineDto>
<e:FinancialPlanLineDto>
<e:AccountDescription>Labor</e:AccountDescription>
<e:AccountKey>key://2/$Account/11086</e:AccountKey>
<e:AccountParentDescription>Account
Structure</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09"/>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2020</f:PeriodDescription>
<f:PeriodKey>key://16/293</f:PeriodKey>
<f:Value>20</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Feb
2020</f:PeriodDescription>
<f:PeriodKey>key://16/294</f:PeriodKey>
<f:Value>15</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2020</f:PeriodDescription>
<f:PeriodKey>key://16/295</f:PeriodKey>
<f:Value>10</f:Value>
</f:EntryDto>
</e:Entries>
<e:LineId>79641</e:LineId>
<e:Note>Line Note for Account:Labor/none</e:Note>
<e:Unit>FTE</e:Unit>
</e:FinancialPlanLineDto>
<e:FinancialPlanLineDto>
<e:AccountDescription>Labor</e:AccountDescription>
<e:AccountKey>key://2/$Account/11086</e:AccountKey>
<e:AccountParentDescription>Account
Structure</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09"/>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
39

PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2020</f:PeriodDescription>
<f:PeriodKey>key://16/293</f:PeriodKey>
<f:Value>58.6666666666667</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Feb
2020</f:PeriodDescription>
<f:PeriodKey>key://16/294</f:PeriodKey>
<f:Value>44</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2020</f:PeriodDescription>
<f:PeriodKey>key://16/295</f:PeriodKey>
<f:Value>29.3333333333333</f:Value>
</f:EntryDto>
</e:Entries>
<e:LineId>79641</e:LineId>
<e:Note>Line Note for Account:Labor/none</e:Note>
<e:Unit>Hours</e:Unit>
</e:FinancialPlanLineDto>
<e:FinancialPlanLineDto>
<e:AccountDescription>Labor</e:AccountDescription>
<e:AccountKey>key://2/$Account/11086</e:AccountKey>
<e:AccountParentDescription>Account
Structure</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09"/>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2020</f:PeriodDescription>
<f:PeriodKey>key://16/293</f:PeriodKey>
<f:Value>5866.67</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Feb
2020</f:PeriodDescription>
<f:PeriodKey>key://16/294</f:PeriodKey>
<f:Value>4400</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2020</f:PeriodDescription>
<f:PeriodKey>key://16/295</f:PeriodKey>
<f:Value>2933.33</f:Value>
</f:EntryDto>
</e:Entries>
<e:LineId>79641</e:LineId>
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
40

<e:Note>Line Note for Account:Labor/none</e:Note>
<e:Unit>Currency</e:Unit>
</e:FinancialPlanLineDto>
<e:FinancialPlanLineDto>
<e:AccountDescription>Hardware</e:AccountDescription>
<e:AccountKey>key://2/$Account/11092</e:AccountKey>
<e:AccountParentDescription>Capital</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09"/>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01"/>
<e:LineId>79643</e:LineId>
<e:Note>Line Note for Account:Capital/Hardware</e:Note>
<e:Unit>Units</e:Unit>
</e:FinancialPlanLineDto>
<e:FinancialPlanLineDto>
<e:AccountDescription>Hardware</e:AccountDescription>
<e:AccountKey>key://2/$Account/11092</e:AccountKey>
<e:AccountParentDescription>Capital</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09"/>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2020</f:PeriodDescription>
<f:PeriodKey>key://16/293</f:PeriodKey>
<f:Value>2000000</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Feb
2020</f:PeriodDescription>
<f:PeriodKey>key://16/294</f:PeriodKey>
<f:Value>2005000</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2020</f:PeriodDescription>
<f:PeriodKey>key://16/295</f:PeriodKey>
<f:Value>2010000</f:Value>
</f:EntryDto>
</e:Entries>
<e:LineId>79643</e:LineId>
<e:Note>Line Note for Account:Capital/Hardware</e:Note>
<e:Unit>Unit Cost</e:Unit>
</e:FinancialPlanLineDto>
<e:FinancialPlanLineDto>
<e:AccountDescription>Hardware</e:AccountDescription>
<e:AccountKey>key://2/$Account/11092</e:AccountKey>
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
41

<e:AccountParentDescription>Capital</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09"/>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2020</f:PeriodDescription>
<f:PeriodKey>key://16/293</f:PeriodKey>
<f:Value>0</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Feb
2020</f:PeriodDescription>
<f:PeriodKey>key://16/294</f:PeriodKey>
<f:Value>0</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2020</f:PeriodDescription>
<f:PeriodKey>key://16/295</f:PeriodKey>
<f:Value>0</f:Value>
</f:EntryDto>
</e:Entries>
<e:LineId>79643</e:LineId>
<e:Note>Line Note for Account:Capital/Hardware</e:Note>
<e:Unit>Currency</e:Unit>
</e:FinancialPlanLineDto>
<e:FinancialPlanLineDto>
<e:AccountDescription>Hardware</e:AccountDescription>
<e:AccountKey>key://2/$Account/11095</e:AccountKey>
<e:AccountParentDescription>Expense</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09">
<f:LineAttributeDto>
<f:AltStructureKey>key://2/$Cost/
14647</f:AltStructureKey>
<f:AltStrucutureDescription>Ohter Hardware
(Expense)</f:AltStrucutureDescription>
</f:LineAttributeDto>
</e:Attributes>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2020</f:PeriodDescription>
<f:PeriodKey>key://16/293</f:PeriodKey>
<f:Value>45000</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Feb
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
42

2020</f:PeriodDescription>
<f:PeriodKey>key://16/294</f:PeriodKey>
<f:Value>46000</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2020</f:PeriodDescription>
<f:PeriodKey>key://16/295</f:PeriodKey>
<f:Value>46500</f:Value>
</f:EntryDto>
</e:Entries>
<e:LineId>79644</e:LineId>
<e:Note>Line Note for Account:Hardware/Expense</e:Note>
<e:Unit>Currency</e:Unit>
</e:FinancialPlanLineDto>
</d:Lines>
<d:ModelDescription>Documentation Financial
Model</d:ModelDescription>
<d:Note>Financial Plan Level Note</d:Note>
<d:VersionDescription>Documentation Financial Version -
Actual</d:VersionDescription>
<d:VersionKey>key://14/96</d:VersionKey>
</c:Dto>
<c:LogTransactionId i:nil="true"/>
</b:OpenSuiteStatus>
</a:Successes>
<a:Warnings xmlns:b="http://schemas.planview.com/PlanviewEnterprise/
OpenSuite/OpenSuiteStatus/2010/01/01"/>
</ReadResult>
</ReadResponse>
</s:Body>
</s:Envelope>
Read - Example 2: Read the Financial Plan Updated in Example 2 of SoapUI
Upsert Examples.
•Use key URIs in the EntityKey and V ersionKey fields to identify the financial plan.
Request
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
xmlns:ns="http://schemas.planview.com/PlanviewEnterprise/Services/FinancialPlan2/
2012/09"
xmlns:ns1="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/
FinancialPlanDto/2013/03"
xmlns:ns2="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/
FinancialPlanLineDto/2013/03"
xmlns:ns3="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/
LineAttributeDto/2012/09"
xmlns:ns4="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/EntryDto/
2010/01/01">
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
43

<soapenv:Header/>
<soapenv:Body>
<ns:Read>
<ns:dtos>
<ns1:FinancialPlanDto>
<ns1:EntityKey>key://2/$Plan/19138</ns1:EntityKey>
<ns1:VersionKey>key://14/96</ns1:VersionKey>
</ns1:FinancialPlanDto>
</ns:dtos>
</ns:Read>
</soapenv:Body>
</soapenv:Envelope>
ResponseResponse
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
<s:Body>
<ReadResponse xmlns="http://schemas.planview.com/PlanviewEnterprise/Services/
FinancialPlan2/2012/09">
<ReadResult xmlns:a="http://schemas.planview.com/PlanviewEnterprise/
OpenSuite/OpenSuiteResult/2010/01/01"
xmlns:i="http://www.w3.org/2001/XMLSchema-instance">
<a:Failures xmlns:b="http://schemas.planview.com/PlanviewEnterprise/
OpenSuite/OpenSuiteStatus/2010/01/01"/>
<a:GeneralErrorMessage i:nil="true"/>
<a:Successes xmlns:b="http://schemas.planview.com/PlanviewEnterprise/
OpenSuite/OpenSuiteStatus/2010/01/01">
<b:OpenSuiteStatus i:type="c:FinancialPlanStatus"
xmlns:c="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/
FinancialPlanStatus/2013/01">
<b:Code i:nil="true"/>
<b:ErrorMessage i:nil="true"/>
<b:SourceIndex>0</b:SourceIndex>
<c:Dto xmlns:d="http://schemas.planview.com/PlanviewEnterprise/
OpenSuite/Dtos/FinancialPlanDto/2013/03">
<d:EntityDescription>Documentation: Project for Financial
Plan</d:EntityDescription>
<d:EntityKey>key://2/$Plan/19138</d:EntityKey>
<d:Key>key://12/2942</d:Key>
<d:Lines xmlns:e="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/FinancialPlanLineDto/2013/03">
<e:FinancialPlanLineDto>
<e:AccountDescription>Revenue</e:AccountDescription>
<e:AccountKey>key://2/$Account/11090</e:AccountKey>
<e:AccountParentDescription>Benefit</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09">
<f:LineAttributeDto>
<f:AltStructureKey>key://2/AGR3/
1403</f:AltStructureKey>
<f:AltStrucutureDescription>ADP</f:AltStrucutureDescription>
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
44

</f:LineAttributeDto>
<f:LineAttributeDto>
<f:AltStructureKey>key://2/Cbs1/
11038</f:AltStructureKey>
<f:AltStrucutureDescription>0198
Networking</f:AltStrucutureDescription>
</f:LineAttributeDto>
</e:Attributes>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2020</f:PeriodDescription>
<f:PeriodKey>key://16/293</f:PeriodKey>
<f:Value>10100</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Feb
2020</f:PeriodDescription>
<f:PeriodKey>key://16/294</f:PeriodKey>
<f:Value>10500</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2020</f:PeriodDescription>
<f:PeriodKey>key://16/295</f:PeriodKey>
<f:Value>12000</f:Value>
</f:EntryDto>
</e:Entries>
<e:LineId>79642</e:LineId>
<e:Note>Updated existing revenue info including adding
revenue for February 2020</e:Note>
<e:Unit>Units</e:Unit>
</e:FinancialPlanLineDto>
<e:FinancialPlanLineDto>
<e:AccountDescription>Revenue</e:AccountDescription>
<e:AccountKey>key://2/$Account/11090</e:AccountKey>
<e:AccountParentDescription>Benefit</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09">
<f:LineAttributeDto>
<f:AltStructureKey>key://2/AGR3/
1403</f:AltStructureKey>
<f:AltStrucutureDescription>ADP</f:AltStrucutureDescription>
</f:LineAttributeDto>
<f:LineAttributeDto>
<f:AltStructureKey>key://2/Cbs1/
11038</f:AltStructureKey>
<f:AltStrucutureDescription>0198
Networking</f:AltStrucutureDescription>
</f:LineAttributeDto>
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
45

</e:Attributes>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2020</f:PeriodDescription>
<f:PeriodKey>key://16/293</f:PeriodKey>
<f:Value>50</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Feb
2020</f:PeriodDescription>
<f:PeriodKey>key://16/294</f:PeriodKey>
<f:Value>55</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2020</f:PeriodDescription>
<f:PeriodKey>key://16/295</f:PeriodKey>
<f:Value>60</f:Value>
</f:EntryDto>
</e:Entries>
<e:LineId>79642</e:LineId>
<e:Note>Updated existing revenue info including adding
revenue for February 2020</e:Note>
<e:Unit>Unit Price</e:Unit>
</e:FinancialPlanLineDto>
<e:FinancialPlanLineDto>
<e:AccountDescription>Revenue</e:AccountDescription>
<e:AccountKey>key://2/$Account/11090</e:AccountKey>
<e:AccountParentDescription>Benefit</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09">
<f:LineAttributeDto>
<f:AltStructureKey>key://2/AGR3/
1403</f:AltStructureKey>
<f:AltStrucutureDescription>ADP</f:AltStrucutureDescription>
</f:LineAttributeDto>
<f:LineAttributeDto>
<f:AltStructureKey>key://2/Cbs1/
11038</f:AltStructureKey>
<f:AltStrucutureDescription>0198
Networking</f:AltStrucutureDescription>
</f:LineAttributeDto>
</e:Attributes>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2020</f:PeriodDescription>
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
46

<f:PeriodKey>key://16/293</f:PeriodKey>
<f:Value>505000</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Feb
2020</f:PeriodDescription>
<f:PeriodKey>key://16/294</f:PeriodKey>
<f:Value>577500</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2020</f:PeriodDescription>
<f:PeriodKey>key://16/295</f:PeriodKey>
<f:Value>720000</f:Value>
</f:EntryDto>
</e:Entries>
<e:LineId>79642</e:LineId>
<e:Note>Updated existing revenue info including adding
revenue for February 2020</e:Note>
<e:Unit>Currency</e:Unit>
</e:FinancialPlanLineDto>
<e:FinancialPlanLineDto>
<e:AccountDescription>Labor</e:AccountDescription>
<e:AccountKey>key://2/$Account/11086</e:AccountKey>
<e:AccountParentDescription>Account
Structure</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09"/>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2020</f:PeriodDescription>
<f:PeriodKey>key://16/293</f:PeriodKey>
<f:Value>20</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Feb
2020</f:PeriodDescription>
<f:PeriodKey>key://16/294</f:PeriodKey>
<f:Value>15</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2020</f:PeriodDescription>
<f:PeriodKey>key://16/295</f:PeriodKey>
<f:Value>10</f:Value>
</f:EntryDto>
</e:Entries>
<e:LineId>79641</e:LineId>
<e:Note>Line Note for Account:Labor/none</e:Note>
<e:Unit>FTE</e:Unit>
</e:FinancialPlanLineDto>
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
47

<e:FinancialPlanLineDto>
<e:AccountDescription>Labor</e:AccountDescription>
<e:AccountKey>key://2/$Account/11086</e:AccountKey>
<e:AccountParentDescription>Account
Structure</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09"/>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2020</f:PeriodDescription>
<f:PeriodKey>key://16/293</f:PeriodKey>
<f:Value>58.6666666666667</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Feb
2020</f:PeriodDescription>
<f:PeriodKey>key://16/294</f:PeriodKey>
<f:Value>44</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2020</f:PeriodDescription>
<f:PeriodKey>key://16/295</f:PeriodKey>
<f:Value>29.3333333333333</f:Value>
</f:EntryDto>
</e:Entries>
<e:LineId>79641</e:LineId>
<e:Note>Line Note for Account:Labor/none</e:Note>
<e:Unit>Hours</e:Unit>
</e:FinancialPlanLineDto>
<e:FinancialPlanLineDto>
<e:AccountDescription>Labor</e:AccountDescription>
<e:AccountKey>key://2/$Account/11086</e:AccountKey>
<e:AccountParentDescription>Account
Structure</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09"/>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2020</f:PeriodDescription>
<f:PeriodKey>key://16/293</f:PeriodKey>
<f:Value>5866.67</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Feb
2020</f:PeriodDescription>
<f:PeriodKey>key://16/294</f:PeriodKey>
<f:Value>4400</f:Value>
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
48

</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2020</f:PeriodDescription>
<f:PeriodKey>key://16/295</f:PeriodKey>
<f:Value>2933.33</f:Value>
</f:EntryDto>
</e:Entries>
<e:LineId>79641</e:LineId>
<e:Note>Line Note for Account:Labor/none</e:Note>
<e:Unit>Currency</e:Unit>
</e:FinancialPlanLineDto>
<e:FinancialPlanLineDto>
<e:AccountDescription>Hardware</e:AccountDescription>
<e:AccountKey>key://2/$Account/11092</e:AccountKey>
<e:AccountParentDescription>Capital</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09"/>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01"/>
<e:LineId>79643</e:LineId>
<e:Note>Line Note for Account:Capital/Hardware</e:Note>
<e:Unit>Units</e:Unit>
</e:FinancialPlanLineDto>
<e:FinancialPlanLineDto>
<e:AccountDescription>Hardware</e:AccountDescription>
<e:AccountKey>key://2/$Account/11092</e:AccountKey>
<e:AccountParentDescription>Capital</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09"/>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2020</f:PeriodDescription>
<f:PeriodKey>key://16/293</f:PeriodKey>
<f:Value>2000000</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Feb
2020</f:PeriodDescription>
<f:PeriodKey>key://16/294</f:PeriodKey>
<f:Value>2005000</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2020</f:PeriodDescription>
<f:PeriodKey>key://16/295</f:PeriodKey>
<f:Value>2010000</f:Value>
</f:EntryDto>
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
49

</e:Entries>
<e:LineId>79643</e:LineId>
<e:Note>Line Note for Account:Capital/Hardware</e:Note>
<e:Unit>Unit Cost</e:Unit>
</e:FinancialPlanLineDto>
<e:FinancialPlanLineDto>
<e:AccountDescription>Hardware</e:AccountDescription>
<e:AccountKey>key://2/$Account/11092</e:AccountKey>
<e:AccountParentDescription>Capital</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09"/>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2020</f:PeriodDescription>
<f:PeriodKey>key://16/293</f:PeriodKey>
<f:Value>0</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Feb
2020</f:PeriodDescription>
<f:PeriodKey>key://16/294</f:PeriodKey>
<f:Value>0</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2020</f:PeriodDescription>
<f:PeriodKey>key://16/295</f:PeriodKey>
<f:Value>0</f:Value>
</f:EntryDto>
</e:Entries>
<e:LineId>79643</e:LineId>
<e:Note>Line Note for Account:Capital/Hardware</e:Note>
<e:Unit>Currency</e:Unit>
</e:FinancialPlanLineDto>
<e:FinancialPlanLineDto>
<e:AccountDescription>Hardware</e:AccountDescription>
<e:AccountKey>key://2/$Account/11095</e:AccountKey>
<e:AccountParentDescription>Expense</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09">
<f:LineAttributeDto>
<f:AltStructureKey>key://2/$Cost/
14647</f:AltStructureKey>
<f:AltStrucutureDescription>Ohter Hardware
(Expense)</f:AltStrucutureDescription>
</f:LineAttributeDto>
</e:Attributes>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
50

PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2020</f:PeriodDescription>
<f:PeriodKey>key://16/293</f:PeriodKey>
<f:Value>45000</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Feb
2020</f:PeriodDescription>
<f:PeriodKey>key://16/294</f:PeriodKey>
<f:Value>46000</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2020</f:PeriodDescription>
<f:PeriodKey>key://16/295</f:PeriodKey>
<f:Value>46500</f:Value>
</f:EntryDto>
</e:Entries>
<e:LineId>79644</e:LineId>
<e:Note>Line Note for Account:Hardware/Expense</e:Note>
<e:Unit>Currency</e:Unit>
</e:FinancialPlanLineDto>
</d:Lines>
<d:ModelDescription>Documentation Financial
Model</d:ModelDescription>
<d:Note>Updated Financial Plan Level Note</d:Note>
<d:VersionDescription>Documentation Financial Version -
Actual</d:VersionDescription>
<d:VersionKey>key://14/96</d:VersionKey>
</c:Dto>
<c:LogTransactionId i:nil="true"/>
</b:OpenSuiteStatus>
</a:Successes>
<a:Warnings xmlns:b="http://schemas.planview.com/PlanviewEnterprise/
OpenSuite/OpenSuiteStatus/2010/01/01"/>
</ReadResult>
</ReadResponse>
</s:Body>
</s:Envelope>
Read – Example 3: Read the Financial Plan in Example 3 of SoapUI Upsert
Examples, Which Clears Editable Fields in a Specified Period Range
•Read the r esults fr om Upsert Example 3 which r emoves all editable fields fr om January 2020 to Mar ch 2020 for all
account types except ACTP$LAB and ACTP$CAP (Labor and Capital).
•A key URI in the Key field was used to identify the financial plan.
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
51

Request
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
xmlns:ns="http://schemas.planview.com/PlanviewEnterprise/Services/FinancialPlan2/
2012/09" xmlns:ns1="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/
FinancialPlanDto/2013/03" xmlns:ns2="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/FinancialPlanLineDto/2013/03"
xmlns:ns3="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/
LineAttributeDto/2012/09" xmlns:ns4="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<soapenv:Header/>
<soapenv:Body>
<ns:Read>
<ns:dtos>
<ns1:FinancialPlanDto>
<ns1:Key>key://12/2942</ns1:Key>
</ns1:FinancialPlanDto>
</ns:dtos>
</ns:Read>
</soapenv:Body>
</soapenv:Envelope>
ResponseResponse
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
<s:Body>
<ReadResponse xmlns="http://schemas.planview.com/PlanviewEnterprise/Services/
FinancialPlan2/2012/09">
<ReadResult xmlns:a="http://schemas.planview.com/PlanviewEnterprise/
OpenSuite/OpenSuiteResult/2010/01/01"
xmlns:i="http://www.w3.org/2001/XMLSchema-instance">
<a:Failures xmlns:b="http://schemas.planview.com/PlanviewEnterprise/
OpenSuite/OpenSuiteStatus/2010/01/01"/>
<a:GeneralErrorMessage i:nil="true"/>
<a:Successes xmlns:b="http://schemas.planview.com/PlanviewEnterprise/
OpenSuite/OpenSuiteStatus/2010/01/01">
<b:OpenSuiteStatus i:type="c:FinancialPlanStatus"
xmlns:c="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/
FinancialPlanStatus/2013/01">
<b:Code i:nil="true"/>
<b:ErrorMessage i:nil="true"/>
<b:SourceIndex>0</b:SourceIndex>
<c:Dto xmlns:d="http://schemas.planview.com/PlanviewEnterprise/
OpenSuite/Dtos/FinancialPlanDto/2013/03">
<d:EntityDescription>Documentation: Project for Financial
Plan</d:EntityDescription>
<d:EntityKey>key://2/$Plan/19138</d:EntityKey>
<d:Key>key://12/2942</d:Key>
<d:Lines xmlns:e="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/FinancialPlanLineDto/2013/03">
<e:FinancialPlanLineDto>
<e:AccountDescription>Revenue</e:AccountDescription>
<e:AccountKey>key://2/$Account/11090</e:AccountKey>
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
52

<e:AccountParentDescription>Benefit</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09">
<f:LineAttributeDto>
<f:AltStructureKey>key://2/AGR3/
1403</f:AltStructureKey>
<f:AltStrucutureDescription>ADP</f:AltStrucutureDescription>
</f:LineAttributeDto>
<f:LineAttributeDto>
<f:AltStructureKey>key://2/Cbs1/
11038</f:AltStructureKey>
<f:AltStrucutureDescription>0198
Networking</f:AltStrucutureDescription>
</f:LineAttributeDto>
</e:Attributes>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01"/>
<e:LineId>79642</e:LineId>
<e:Note>Updated existing revenue info including adding
revenue for February 2020</e:Note>
<e:Unit>Units</e:Unit>
</e:FinancialPlanLineDto>
<e:FinancialPlanLineDto>
<e:AccountDescription>Revenue</e:AccountDescription>
<e:AccountKey>key://2/$Account/11090</e:AccountKey>
<e:AccountParentDescription>Benefit</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09">
<f:LineAttributeDto>
<f:AltStructureKey>key://2/AGR3/
1403</f:AltStructureKey>
<f:AltStrucutureDescription>ADP</f:AltStrucutureDescription>
</f:LineAttributeDto>
<f:LineAttributeDto>
<f:AltStructureKey>key://2/Cbs1/
11038</f:AltStructureKey>
<f:AltStrucutureDescription>0198
Networking</f:AltStrucutureDescription>
</f:LineAttributeDto>
</e:Attributes>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01"/>
<e:LineId>79642</e:LineId>
<e:Note>Updated existing revenue info including adding
revenue for February 2020</e:Note>
<e:Unit>Unit Price</e:Unit>
</e:FinancialPlanLineDto>
<e:FinancialPlanLineDto>
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
53

<e:AccountDescription>Revenue</e:AccountDescription>
<e:AccountKey>key://2/$Account/11090</e:AccountKey>
<e:AccountParentDescription>Benefit</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09">
<f:LineAttributeDto>
<f:AltStructureKey>key://2/AGR3/
1403</f:AltStructureKey>
<f:AltStrucutureDescription>ADP</f:AltStrucutureDescription>
</f:LineAttributeDto>
<f:LineAttributeDto>
<f:AltStructureKey>key://2/Cbs1/
11038</f:AltStructureKey>
<f:AltStrucutureDescription>0198
Networking</f:AltStrucutureDescription>
</f:LineAttributeDto>
</e:Attributes>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01"/>
<e:LineId>79642</e:LineId>
<e:Note>Updated existing revenue info including adding
revenue for February 2020</e:Note>
<e:Unit>Currency</e:Unit>
</e:FinancialPlanLineDto>
<e:FinancialPlanLineDto>
<e:AccountDescription>Labor</e:AccountDescription>
<e:AccountKey>key://2/$Account/11086</e:AccountKey>
<e:AccountParentDescription>Account
Structure</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09"/>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2020</f:PeriodDescription>
<f:PeriodKey>key://16/293</f:PeriodKey>
<f:Value>20</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Feb
2020</f:PeriodDescription>
<f:PeriodKey>key://16/294</f:PeriodKey>
<f:Value>15</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2020</f:PeriodDescription>
<f:PeriodKey>key://16/295</f:PeriodKey>
<f:Value>10</f:Value>
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
54

</f:EntryDto>
</e:Entries>
<e:LineId>79641</e:LineId>
<e:Note>Line Note for Account:Labor/none</e:Note>
<e:Unit>FTE</e:Unit>
</e:FinancialPlanLineDto>
<e:FinancialPlanLineDto>
<e:AccountDescription>Labor</e:AccountDescription>
<e:AccountKey>key://2/$Account/11086</e:AccountKey>
<e:AccountParentDescription>Account
Structure</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09"/>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2020</f:PeriodDescription>
<f:PeriodKey>key://16/293</f:PeriodKey>
<f:Value>58.6666666666667</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Feb
2020</f:PeriodDescription>
<f:PeriodKey>key://16/294</f:PeriodKey>
<f:Value>44</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2020</f:PeriodDescription>
<f:PeriodKey>key://16/295</f:PeriodKey>
<f:Value>29.3333333333333</f:Value>
</f:EntryDto>
</e:Entries>
<e:LineId>79641</e:LineId>
<e:Note>Line Note for Account:Labor/none</e:Note>
<e:Unit>Hours</e:Unit>
</e:FinancialPlanLineDto>
<e:FinancialPlanLineDto>
<e:AccountDescription>Labor</e:AccountDescription>
<e:AccountKey>key://2/$Account/11086</e:AccountKey>
<e:AccountParentDescription>Account
Structure</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09"/>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2020</f:PeriodDescription>
<f:PeriodKey>key://16/293</f:PeriodKey>
<f:Value>5866.67</f:Value>
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
55

</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Feb
2020</f:PeriodDescription>
<f:PeriodKey>key://16/294</f:PeriodKey>
<f:Value>4400</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2020</f:PeriodDescription>
<f:PeriodKey>key://16/295</f:PeriodKey>
<f:Value>2933.33</f:Value>
</f:EntryDto>
</e:Entries>
<e:LineId>79641</e:LineId>
<e:Note>Line Note for Account:Labor/none</e:Note>
<e:Unit>Currency</e:Unit>
</e:FinancialPlanLineDto>
<e:FinancialPlanLineDto>
<e:AccountDescription>Hardware</e:AccountDescription>
<e:AccountKey>key://2/$Account/11092</e:AccountKey>
<e:AccountParentDescription>Capital</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09"/>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01"/>
<e:LineId>79643</e:LineId>
<e:Note>Line Note for Account:Capital/Hardware</e:Note>
<e:Unit>Units</e:Unit>
</e:FinancialPlanLineDto>
<e:FinancialPlanLineDto>
<e:AccountDescription>Hardware</e:AccountDescription>
<e:AccountKey>key://2/$Account/11092</e:AccountKey>
<e:AccountParentDescription>Capital</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09"/>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2020</f:PeriodDescription>
<f:PeriodKey>key://16/293</f:PeriodKey>
<f:Value>2000000</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Feb
2020</f:PeriodDescription>
<f:PeriodKey>key://16/294</f:PeriodKey>
<f:Value>2005000</f:Value>
</f:EntryDto>
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
56

<f:EntryDto>
<f:PeriodDescription>Mar
2020</f:PeriodDescription>
<f:PeriodKey>key://16/295</f:PeriodKey>
<f:Value>2010000</f:Value>
</f:EntryDto>
</e:Entries>
<e:LineId>79643</e:LineId>
<e:Note>Line Note for Account:Capital/Hardware</e:Note>
<e:Unit>Unit Cost</e:Unit>
</e:FinancialPlanLineDto>
<e:FinancialPlanLineDto>
<e:AccountDescription>Hardware</e:AccountDescription>
<e:AccountKey>key://2/$Account/11092</e:AccountKey>
<e:AccountParentDescription>Capital</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09"/>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01">
<f:EntryDto>
<f:PeriodDescription>Jan
2020</f:PeriodDescription>
<f:PeriodKey>key://16/293</f:PeriodKey>
<f:Value>0</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Feb
2020</f:PeriodDescription>
<f:PeriodKey>key://16/294</f:PeriodKey>
<f:Value>0</f:Value>
</f:EntryDto>
<f:EntryDto>
<f:PeriodDescription>Mar
2020</f:PeriodDescription>
<f:PeriodKey>key://16/295</f:PeriodKey>
<f:Value>0</f:Value>
</f:EntryDto>
</e:Entries>
<e:LineId>79643</e:LineId>
<e:Note>Line Note for Account:Capital/Hardware</e:Note>
<e:Unit>Currency</e:Unit>
</e:FinancialPlanLineDto>
<e:FinancialPlanLineDto>
<e:AccountDescription>Hardware</e:AccountDescription>
<e:AccountKey>key://2/$Account/11095</e:AccountKey>
<e:AccountParentDescription>Expense</e:AccountParentDescription>
<e:Attributes xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/LineAttributeDto/2012/09">
<f:LineAttributeDto>
<f:AltStructureKey>key://2/$Cost/
14647</f:AltStructureKey>
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
57

<f:AltStrucutureDescription>Ohter Hardware
(Expense)</f:AltStrucutureDescription>
</f:LineAttributeDto>
</e:Attributes>
<e:CurrencyKey>key://1/USD</e:CurrencyKey>
<e:Entries xmlns:f="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01"/>
<e:LineId>79644</e:LineId>
<e:Note>Line Note for Account:Hardware/Expense</e:Note>
<e:Unit>Currency</e:Unit>
</e:FinancialPlanLineDto>
</d:Lines>
<d:ModelDescription>Documentation Financial
Model</d:ModelDescription>
<d:Note>Updated Financial Plan Level Note</d:Note>
<d:VersionDescription>Documentation Financial Version -
Actual</d:VersionDescription>
<d:VersionKey>key://14/96</d:VersionKey>
</c:Dto>
<c:LogTransactionId i:nil="true"/>
</b:OpenSuiteStatus>
</a:Successes>
<a:Warnings xmlns:b="http://schemas.planview.com/PlanviewEnterprise/
OpenSuite/OpenSuiteStatus/2010/01/01"/>
</ReadResult>
</ReadResponse>
</s:Body>
</s:Envelope>
SoapUI Upsert Examples
Upsert – Example 1: Cr eate a financial plan
•This example cr eates a work financial plan utilizing accounts for income, outgo, and labor .
Request
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
xmlns:ns="http://schemas.planview.com/PlanviewEnterprise/Services/FinancialPlan2/
2012/09"
xmlns:ns1="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/
FinancialPlanDto/2013/03"
xmlns:ns2="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/
FinancialPlanLineDto/2013/03"
xmlns:ns3="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/
LineAttributeDto/2012/09"
xmlns:ns4="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/EntryDto/
2010/01/01"
xmlns:ns5="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
58

DeleteEditableFinancialPlanEntriesDto/2013/03"
xmlns:arr="http://schemas.microsoft.com/2003/10/Serialization/Arrays">
<soapenv:Header/>
<soapenv:Body>
<ns:Upsert>
<ns:dtos>
<ns1:FinancialPlanDto>
<ns1:EntityKey>ekey://2/Documentation/Project_for_Financial_
Plan</ns1:EntityKey>
<ns1:Key>ekey://12/Documentation/Financial_Plan</ns1:Key>
<ns1:Lines>
<!-- Add a Benefit/Revenue account. Provide the number of units and per unit price.
-->
<!-- Benefit/Revenue number of units -->
<ns2:FinancialPlanLineDto>
<ns2:AccountKey>key://2/$Account/11090</ns2:AccountKey>
<ns2:Attributes>
<ns3:LineAttributeDto>
<ns3:AltStructureKey>key://2/AGR3/
1403</ns3:AltStructureKey>
</ns3:LineAttributeDto>
<ns3:LineAttributeDto>
<ns3:AltStructureKey>key://2/Cbs1/
11038</ns3:AltStructureKey>
</ns3:LineAttributeDto>
</ns2:Attributes>
<ns2:CurrencyKey>key://1/USD</ns2:CurrencyKey>
<ns2:Entries>
<ns4:EntryDto>
<ns4:PeriodKey>key://16/293</ns4:PeriodKey>
<ns4:Value>10000</ns4:Value>
</ns4:EntryDto>
<!-- The entry for February 2020 (Period ID 294) was left out
to demonstrate skipping entries-->
<ns4:EntryDto>
<ns4:PeriodKey>key://16/295</ns4:PeriodKey>
<ns4:Value>12000</ns4:Value>
</ns4:EntryDto>
</ns2:Entries>
<ns2:Note>Line Note for Account:Benefit/Revenue</ns2:Note>
<ns2:Unit>Units</ns2:Unit>
</ns2:FinancialPlanLineDto>
<!-- Benefit/Revenue unit price -->
<ns2:FinancialPlanLineDto>
<ns2:AccountKey>key://2/$Account/11090</ns2:AccountKey>
<ns2:Attributes>
<ns3:LineAttributeDto>
<ns3:AltStructureKey>key://2/AGR3/
1403</ns3:AltStructureKey>
</ns3:LineAttributeDto>
<ns3:LineAttributeDto>
<ns3:AltStructureKey>key://2/Cbs1/
11038</ns3:AltStructureKey>
</ns3:LineAttributeDto>
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
59

</ns2:Attributes>
<ns2:CurrencyKey>key://1/USD</ns2:CurrencyKey>
<ns2:Entries>
<ns4:EntryDto>
<ns4:PeriodKey>key://16/293</ns4:PeriodKey>
<ns4:Value>50</ns4:Value>
</ns4:EntryDto>
<!-- The entry for February 2020 (key://16/294) was left out
to demonstrate skipping entries -->
<ns4:EntryDto>
<ns4:PeriodKey>key://16/295</ns4:PeriodKey>
<ns4:Value>60</ns4:Value>
</ns4:EntryDto>
</ns2:Entries>
<ns2:Note>Line Note for Account:Benefit/
Revenue</ns2:Note>
<ns2:Unit>Unit Price</ns2:Unit>
</ns2:FinancialPlanLineDto>
<!-- Add a Labor account. Provide the number of FTE.-->
<ns2:FinancialPlanLineDto>
<ns2:AccountKey>key://2/$Account/
11086</ns2:AccountKey>
<ns2:CurrencyKey>key://1/USD</ns2:CurrencyKey>
<ns2:Entries>
<ns4:EntryDto>
<ns4:PeriodKey>key://16/293</ns4:PeriodKey>
<ns4:Value>20</ns4:Value>
</ns4:EntryDto>
<ns4:EntryDto>
<ns4:PeriodKey>key://16/294</ns4:PeriodKey>
<ns4:Value>15</ns4:Value>
</ns4:EntryDto>                        <ns4:EntryDto>
<ns4:PeriodKey>key://16/295</ns4:PeriodKey>
<ns4:Value>10</ns4:Value>
</ns4:EntryDto>
</ns2:Entries>
<ns2:Note>Line Note for Account:Labor/none</ns2:Note>
<ns2:Unit>FTE</ns2:Unit>
</ns2:FinancialPlanLineDto>
<!-- Add a Capital/Hardware account. Provide the number of units and units cost -->
<!-- Capital/Hardware number of units -->
<ns2:FinancialPlanLineDto>
<ns2:AccountKey>key://2/$Account/
11092</ns2:AccountKey>
<ns2:CurrencyKey>key://1/USD</ns2:CurrencyKey>
<ns2:Entries>
<ns4:EntryDto>
<ns4:PeriodKey>key://16/293</ns4:PeriodKey>
<ns4:Value>2000000</ns4:Value>
</ns4:EntryDto>
<ns4:EntryDto>
<ns4:PeriodKey>key://16/294</ns4:PeriodKey>
<ns4:Value>2005000</ns4:Value>
</ns4:EntryDto>                        <ns4:EntryDto>
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
60

<ns4:PeriodKey>key://16/295</ns4:PeriodKey>
<ns4:Value>2010000</ns4:Value>
</ns4:EntryDto>
</ns2:Entries>
<ns2:Note>Line Note for Account:Capital/Hardware </ns2:Note>
<ns2:Unit>Unit Cost</ns2:Unit>
</ns2:FinancialPlanLineDto>
<!-- Add an Expense/Hardware account. Provide the total cost in USD. -->
<ns2:FinancialPlanLineDto>
<ns2:AccountKey>key://2/$Account/11095</ns2:AccountKey>
<ns2:Attributes>
<ns3:LineAttributeDto>
<ns3:AltStructureKey>key://2/$Cost/
14647</ns3:AltStructureKey>
</ns3:LineAttributeDto>
</ns2:Attributes>
<ns2:CurrencyKey>key://1/USD</ns2:CurrencyKey>
<ns2:Entries>
<ns4:EntryDto>
<ns4:PeriodKey>key://16/293</ns4:PeriodKey>
<ns4:Value>45000</ns4:Value>
</ns4:EntryDto>
<ns4:EntryDto>
<ns4:PeriodKey>key://16/294</ns4:PeriodKey>
<ns4:Value>46000</ns4:Value>
</ns4:EntryDto>
<ns4:EntryDto>
<ns4:PeriodKey>key://16/295</ns4:PeriodKey>
<ns4:Value>46500</ns4:Value>
</ns4:EntryDto>
</ns2:Entries>
<ns2:Note>Line Note for Account:Hardware/Expense</ns2:Note>
<ns2:Unit>Currency</ns2:Unit>
</ns2:FinancialPlanLineDto>
</ns1:Lines>
<ns1:Note>Financial Plan Level Note</ns1:Note>
<ns1:VersionKey>key://14/96</ns1:VersionKey>
</ns1:FinancialPlanDto>
</ns:dtos>
</ns:Upsert>
</soapenv:Body>
</soapenv:Envelope>
Upsert – Example 2: Update a Financial Plan
•Update the financial plan cr eated in Example 1.
•We do not have to put the entir e plan in the r equest. The following r equest incr eases the number of Revenue units
for January 2020 (period 293) fr om 10000 to 10100 and adds the missing r evenue for February 2020 (period 294).
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
61

Request
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
xmlns:ns="http://schemas.planview.com/PlanviewEnterprise/Services/FinancialPlan2/
2012/09" xmlns:ns1="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/
FinancialPlanDto/2013/03" xmlns:ns2="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/FinancialPlanLineDto/2013/03"
xmlns:ns3="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/
LineAttributeDto/2012/09" xmlns:ns4="http://schemas.planview.com/
PlanviewEnterprise/OpenSuite/Dtos/EntryDto/2010/01/01" xmlns:ns5="http://schemas.
planview.com/PlanviewEnterprise/OpenSuite/Dtos/
DeleteEditableFinancialPlanEntriesDto/2013/03" xmlns:arr="http://schemas.microsoft.
com/2003/10/Serialization/Arrays">
<soapenv:Header/>
<soapenv:Body>
<ns:Upsert>
<ns:dtos>
<ns1:FinancialPlanDto>
<ns1:EntityKey>eKey://2/Documentation/Project_for_Financial_
Plan</ns1:EntityKey>
<ns1:Lines>
<!-- Add a Benefit/Revenue account. Provide the number of units and per unit price.
-->
<!-- Benefit/Revenue number of units -->
<ns2:FinancialPlanLineDto>
<ns2:AccountKey>key://2/$Account/11090</ns2:AccountKey>
<ns2:Attributes>
<ns3:LineAttributeDto>
<ns3:AltStructureKey>key://2/AGR3/
1403</ns3:AltStructureKey>
</ns3:LineAttributeDto>
<ns3:LineAttributeDto>
<ns3:AltStructureKey>key://2/Cbs1/
11038</ns3:AltStructureKey>
</ns3:LineAttributeDto>
</ns2:Attributes>
<ns2:CurrencyKey>key://1/USD</ns2:CurrencyKey>
<ns2:Entries>
<ns4:EntryDto>
<ns4:PeriodKey>key://16/293</ns4:PeriodKey>
<ns4:Value>10100</ns4:Value>
</ns4:EntryDto>
<ns4:EntryDto>
<ns4:PeriodKey>key://16/294</ns4:PeriodKey>
<ns4:Value>10500</ns4:Value>
</ns4:EntryDto>
<!-- The entry for March 2020 (Period ID 295) was left out in this example as it
is not being updated. Leaving it out is optional.-->
</ns2:Entries>
<ns2:Note>Updated existing revenue info including adding
revenue for February 2020</ns2:Note>
<ns2:Unit>Units</ns2:Unit>
</ns2:FinancialPlanLineDto>
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
62

<!-- Benefit/Revenue unit price -->
<ns2:FinancialPlanLineDto>
<ns2:AccountKey>key://2/$Account/11090</ns2:AccountKey>
<ns2:Attributes>
<ns3:LineAttributeDto>
<ns3:AltStructureKey>key://2/AGR3/
1403</ns3:AltStructureKey>
</ns3:LineAttributeDto>
<ns3:LineAttributeDto>
<ns3:AltStructureKey>key://2/Cbs1/
11038</ns3:AltStructureKey>
</ns3:LineAttributeDto>
</ns2:Attributes>
<ns2:CurrencyKey>key://1/USD</ns2:CurrencyKey>
<ns2:Entries>
<!-- The entries for January and March 2020 (Period IDs 293 and 294) were left out
in this example as they were not being updated. Leaving them out is optional.-->
<ns4:EntryDto>
<ns4:PeriodKey>key://16/294</ns4:PeriodKey>
<ns4:Value>55</ns4:Value>
</ns4:EntryDto>
</ns2:Entries>
<ns2:Note>Updated existing revenue info including adding
revenue for February 2020</ns2:Note>
<ns2:Unit>Unit Price</ns2:Unit>
</ns2:FinancialPlanLineDto>
</ns1:Lines>
<ns1:Note>Updated Financial Plan Level Note</ns1:Note>
<ns1:VersionKey>key://14/96</ns1:VersionKey>
</ns1:FinancialPlanDto>
</ns:dtos>
</ns:Upsert>
</soapenv:Body>
</soapenv:Envelope>
Upsert –Example 3: Clear Editable Fields in Period Range
•Using the r esults fr om Example 2 above, clear the editable fields in the period range 293 to 295.
•Skip all fields for account types ACTP$LAB and ACTP$EXP .
•You cannot update financial plan notes if your FinancialPlanDto contains 0 lines.
Request
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
xmlns:ns="http://schemas.planview.com/PlanviewEnterprise/Services/FinancialPlan2/
2012/09"
xmlns:ns1="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/
FinancialPlanDto/2013/03"
xmlns:ns2="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/
FinancialPlanLineDto/2013/03"
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
63

xmlns:ns3="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/
LineAttributeDto/2012/09"
xmlns:ns4="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/EntryDto/
2010/01/01"
xmlns:ns5="http://schemas.planview.com/PlanviewEnterprise/OpenSuite/Dtos/
DeleteEditableFinancialPlanEntriesDto/2013/03"
xmlns:arr="http://schemas.microsoft.com/2003/10/Serialization/Arrays">
<soapenv:Header/>
<soapenv:Body>
<ns:Upsert>
<ns:dtos>
<ns1:FinancialPlanDto>
<ns1:Key>ekey://12/Documentation/Financial_Plan</ns1:Key>
</ns1:FinancialPlanDto>
</ns:dtos>
<ns:deleteEditableFinancialPlanEntriesDto>
<ns5:AccountTypesToPreserveKeys>
<arr:string>key://2/AcctType/ACTP$LAB</arr:string>
<arr:string>key://2/AcctType/ACTP$CAP</arr:string>
</ns5:AccountTypesToPreserveKeys>
<ns5:FinalPeriodKey>key://16/295</ns5:FinalPeriodKey>
<ns5:FirstPeriodKey>key://16/293</ns5:FirstPeriodKey>
</ns:deleteEditableFinancialPlanEntriesDto>
</ns:Upsert>
</soapenv:Body>
</soapenv:Envelope>
Methods
Name Description
Read•Use this method to r ead a financial plan.
•Minimum r equir ed fields: Key or V ersionKey and EntityKey
Upsert•Use this method to upsert financial plans.
•Minimum r equir ed fields by DTO:
•FinancialPlanDto: Key (or V ersionKey and EntityKey) and Lines
(with at least 1 FinancialPlanLineDto)
•FinancialPlanLineDto: AccountKey , Attributes (if the account has
any r equir ed attributes), Unit and Entries (with at least 1 EntryDto)
•LineAttributeDto: AltStructur eKey (This DTO is r equir ed only for
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
64

Name Description
accounts with mandatory attributes.)
•EntryDto: PeriodKey and V alue.
NOTE
A financial plan cannot be cr eated or updated unless its
FinancialPlanDto contains at least one valid FinancialPlanLineDto. The
only exception is if you ar e clearing values using the
DeleteEditableFinancialPlanEntriesDto.
Known Issue: It is curr ently possible to cr eate a financial plan with 0 lines.
You cannot do this thr ough the UI and it is consider ed a bug. Do not r ely on
this being possible.
Method: Read
Description
•Use this method to r ead a financial plan.
•Minimum r equir ed fields: Key or V ersionKey and EntityKey .
Parameters
Name Type Direction Description
dtos ArrayOfFinancialPlanDto Input Collection of FinancialPlanDtos DTOs.
Returns
OpenSuiteResult with OpenSuiteStatus sub type of FinancialPlanStatus. FinancialPlanStatus has a DTO field containing
the r esult FinancialPlanDto. If successful the full DTO will be r eturned. On failur e a DTO containing the Key will be
returned. The FinancialPlanStatus.LogT ransactionId is not used by this method.
See the OpenSuiteStatus topic in Getting Started with W eb Services for mor e information.
Method: Upsert
Description
•Use this method to upsert financial plans.
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
65

•Minimum r equir ed fields by DTO:
•FinancialPlanDto: Key (or V ersionKey and EntityKey) and Lines (with at least 1 FinancialPlanLineDto).
•FinancialPlanLineDto: AccountKey , Attributes (if the account has any r equir ed attributes), Unit and Entries (with
at least 1 EntryDto).
•LineAttributeDto: AltStructur eKey (This DTO is r equir ed only for accounts with mandatory attributes).
•EntryDto: PeriodKey and V alue.
NOTE
A financial plan cannot be cr eated or updated unless its FinancialPlanDto contains at least one valid
FinancialPlanLineDto. The only exception is if you ar e clearing values using the
DeleteEditableFinancialPlanEntriesDto.
Known Issue: It is curr ently possible to cr eate a financial plan with 0 lines. Y ou cannot do this thr ough the UI and it is
consider ed a bug. Do not r ely on this being possible.
Parameters
Name Type Direction Description
dtos ArrayOfFinancialPlanDto Input Collection of
FinancialPlanDtos
DTOs.
deleteEditableFinancialPlanEntriesDto DeleteEditableFinancialPlanEntriesDto Input DTO describing which
editable fields to clear
(if any).
Returns
OpenSuiteResult with OpenSuiteStatus subtype of FinancialPlanStatus. FinancialPlanStatus has a field named Dto
containing the r esult FinancialPlanDto. If successful only the Key field of the DTO will be set. On failur e, a full DTO will
be returned. In addition, the FinancialPlanStatus contains a LogT ransactionId field. All err or messages and warnings ar e
provided via the OpenSuiteResult. Y ou can also use the LogT ransactionId to extract r ecords (including INFO r ecords)
written to the pv_pr ocess_log table in the database. However , preprocessing messages such as early missing r equir ed
field and key r esolution messages ar e available only fr om the OpenSuiteResult. T o retrieve the pv_pr ocess_log r ecords,
use the QueryService and r equest all r ecords from the pv_pr ocess_log wher e transaction_id = LogT ransactionId.
See the OpenSuiteStatus topic in Getting Started with W eb Services for mor e information.
Remarks
1Prerequisites
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
66

A financial plan is constructed fr om a financial model/version and a entity (pr oject, or ganizational r esour ce, pr oduct, cost
center , strategy , asset, or service). The lines within the financial plan ar e defined by their financial accounts and
attributes. Befor e you can cr eate a financial plan the following must be true:
•The model exists.
•The version exists for the model.
•The entity must exist.
•Any accounts to be added to the plan must exist and be associated to the model.
•Any line attributes must exist and be associated to the desir ed accounts.
Identifying a Financial Plan via the FinancialPlanDto
You can identify a financial plan by either the Key field alone or by the V ersionKey and EntityKey fields combined. It is no
longer necessary to pr ovide a model as this information is stor ed in the version r ecord.
TIP
To incr ease performance, FinancialPlanService has been optimized to quickly pr ocess all financial plan lines for a
financial plan version as a gr oup. Thus, if you ar e batching r equests, performance should be impr oved if you batch by
financial plan version.
Complex T ypes
Name Description
DeleteEditableFinancialPlanEntriesDto DeleteEditableFinancialPlanEntriesDto is used to specify
the editable fields to be clear ed fr om each financial plan
being updated by this web service r equest.
EntryDto EntryDto is a r epresentation of a financial plan line entry
for use within the interface IFinancialPlanService2 for the
Financial Plan web service. The entry may be for an FTE,
Hours, Unit Cost, Unit Price, or Curr ency (total expense or
income).
FinancialPlanDto FinancialPlanLineDto is a r epresentation of a financial
plan line or a component of a line (see Remarks) for use
within the interface IFinancialPlanService2 for the
Financial Plan web service.
FinancialPlanLineDto FinancialPlanLineDto is a r epresentation of a financial
plan line,1or component of a line,2for use within the
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
67

Name Description
interface IFinancialPlanService2 for the Financial Plan web
service.
LineAttributeDto LineAttributeDto is a r epresentation of a line attribute for
use within the interface IFinancialPlanService2 for the
Financial Plan web service.
Complex T ype: DeleteEditableFinancialPlanEntriesDto
DeleteEditableFinancialPlanEntriesDto is used to specify the editable fields to be clear ed fr om each financial plan being
updated by this web service r equest.
Content Model
Contains elements as defined in the following table.
Field Type Default Editable Description
AccountT ypesT oPreserveKeys ArrayOfstring nil Yes Collection of Structur e key URIs for
structur e name = AccT ype. Entries for
lines with the account types in this list
will not be clear ed. If left null, all
editable fields within the specified
period range will be clear ed.
DB Info : Not stor ed in or r ead fr om
database.
FinalPeriodKey string nil Yes FinancialPlanPeriod key URI for the last
period in the range to be clear ed.
DB Info : Not stor ed in or r ead fr om
database.
FirstPeriodKey string nil Yes FinancialPlanPeriod key URI for the first
period in the range to be clear ed.
DB Info : Not stor ed in or r ead fr om
database.
Remarks
•You can clear a single period by setting FinalPeriodKey and FirstPeriodKey to the same period.
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
68

•You can clear all of the editable fields in a financial plan by defining the period range as the first period in the
financial calendar (period 1) and the last period in the calendar (depends on the calendar).
Complex T ype: EntryDto
EntryDto is a r epresentation of a financial plan line entry for use within the interface IFinancialPlanService2 for the
Financial Plan web service. The entry may be for an FTE, Hours, Unit Cost, Unit Price, or Curr ency (total expense or
income).
Content Model
Contains elements as defined in the following table.
Field Type Default Editable Description
PeriodDescription string n/a No Read only period description.
DB Info :
•Months:
fm_period.epm_period_description
converted fr om integer to month
description +
fm_period.epm_year_description
•Quarters: fm_period.period_type +
fm_period.epm_period_description +
fm_period.epm_year_description
•Years: fm_period.epm_year_description
PeriodKey string nil Yes FinancialPlanPeriod key URI for the financial
period.
•The period specified must be within the
horizon of the financial plan.
•You can specify a Month, Quarter , or Y ear
period.
DB Info : fm_budget_entry .period_id
Value double nil Yes Numeric value of the entry .
DB Info : See r emarks.
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
69

Remarks
Value DB Info
A single fm_budget_entry r ecord may be comprised fr om data (all for the same period) fr om up to thr ee
FinancialPlanLineDtos, each with a dif ferent Unit type. Each Unit type on the FinancialPlanDto indicates to which field
the V alue on the line’ s FinancialPlanEntryDtos will map. However , the mapping may not be dir ect. For instance, V alue for
a multi-month period will be spr ead over the constituent editable monthly periods as all entry data is stor ed by monthly
period. The following tables ar e not intended to pr esent the complete rule set for financial plan entries, but rather a
general description of wher e the values fr om the entries ar e placed in the database.
Note : fm_budget.budget_id = fm_budget_line.budget_id, fm_budget_line.line_id = fm_budget_entry .line_id
Unit for non-Labor Accounts DB FieldCalculate Currency (total cost or
total quantity)
Units fm_budget_entry .qty Calculate Curr ency …
•Field is editable.
•Cost override is allowed.
•ShowCost is enabled and
fm_budget_entry .rate is set in the
database.
Unit Price, Unit Cost fm_budget_entry .rate
Calculate Curr ency …
•Field is editable.
•Cost override is allowed.
•ShowCost is enabled and
fm_budget_entry .qty is set in the
database.
Currency fm_budget_entry .amount
Unit for Labor Accounts
FTE Used to calculate ef fort in minutes
which is stor ed in
budget_line_entry .qtyCalculate Curr ency if …
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
70

Unit for Labor Accounts
•Field is editable.
•Cost override is allowed.
•A rate can be found in the rates
tables.
Hours Used to calculate ef fort in minutes
which is stor ed in
budget_line_entry .qtyCalculate Curr ency if …
•Field is editable.
•Cost override is allowed.
•A rate can be found in the rates
tables.
Currency budget_line_entry .amount
Complex T ype: FinancialPlanDto
FinancialPlanLineDto is a r epresentation of a financial plan line or a component of a line (see Remarks) for use within the
interface IFinancialPlanService2 for the Financial Plan web service.
Content Model
Contains elements as defined in the following table.
Field Type Default Editable Description
EntityDescription string (50) n/a No Description of the work, or ganizational
resour ce, pr oduct, cost center , strategy , asset,
or service entity associated with this financial
plan.
DB.Info : structur e.description
(fm_budget.structur e_code =
structur e.structur e_code)
EntityKey string nil Yes Structur e key URI for the entity associated
with this financial plan.
Structur e name = $Plan, $Or gRes, $Pr od,
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
71

Field Type Default Editable Description
Cbs1, $Strategy , $Asset or $Service.
DB Info : fm_budget.structur e_code
Key string nil Yes FinancialPlan key URI for this financial plan.
DB Info : fm_budget.budget_id
Lines ArrayOfFinancialPlanLineDto nil Yes A collection of FinancialPlanLineDtos that
provide information needed to add new or
update existing lines in the financial plan.
DB Info : fm_budget_line.line_id
(fm_budget.budget_id =
fm_budget_line.budget_id)
ModelDescription string (50) n/a No Read only description of the Model
associated with this financial plan.
DB Info : fm_model.model_description
(fm_budget.version_id =
fm_version.version_id, fm_version.model_id
= fm_model.model_id)
Note string (4000) n/a Yes String containing information about the
financial plan.1
DB Info: fm_budget.note
VersionDescription string (50) n/a No Read only description of the V ersion of the
financial plan.
DB Info : fm_version.version_description
(fm_budget.version_id =
fm_version.version_id)
VersionKey string nil Yes FinancailPlanV ersion key URI of this version of
the financial plan.
DB Info : fm_version.version_id,
(fm_budget.version_id =
fm_version.version_id)
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
72

Remarks
1Note
•Anote cannot contain unencoded special characters that can be interpr eted as XML/HTML, etc. This will cause a
deserialization err or and the financial plan will not be pr ocessed. The note will be interpr eted as plain text. Any
formatting characters will be tr eated as text.
•You cannot completely delete a note. Setting the note to "" or null will not update the note.
Field Type Default Editable Description
EntityDescription string (50) n/a No Description of the work,
organizational r esour ce, pr oduct,
cost center , strategy , asset, or service
entity associated with this financial
plan.
DB.Info : structur e.description
(fm_budget.structur e_code =
structur e.structur e_code)
EntityKey string nil Yes Structur e key URI for the entity
associated with this financial plan.
Structur e name = $Plan, $Or gRes,
$Prod, Cbs1, $Strategy , $Asset or
$Service.
DB Info : fm_budget.structur e_code
Key string nil Yes FinancialPlan key URI for this financial
plan.
DB Info : fm_budget.budget_id
Lines ArrayOfFinancialPlanLineDto nil Yes A collection of
FinancialPlanLineDtos that pr ovide
information needed to add new or
update existing lines in the financial
plan.
DB Info : fm_budget_line.line_id
(fm_budget.budget_id =
fm_budget_line.budget_id)
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
73

Field Type Default Editable Description
ModelDescription string (50) n/a No Read only description of the Model
associated with this financial plan.
DB Info :
fm_model.model_description
(fm_budget.version_id =
fm_version.version_id,
fm_version.model_id =
fm_model.model_id)
VersionDescription string (50) n/a No Read only description of the V ersion
of the financial plan.
DB Info :
fm_version.version_description
(fm_budget.version_id =
fm_version.version_id)
VersionKey string nil Yes FinancailPlanV ersion key URI of this
version of the financial plan.
DB Info : fm_version.version_id,
(fm_budget.version_id =
fm_version.version_id)
Complex T ype: FinancialPlanLineDto
FinancialPlanLineDto is a r epresentation of a financial plan line,1or component of a line,2for use within the interface
IFinancialPlanService2 for the Financial Plan web service.
Content Model
Contains elements as defined in the following table.
Field Type Default Editable Description
AccountDescription string (50) n/a No Read only description of the account
associated with this line.
DB Info : structur e.description
(fm_budget.budget_id =
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
74

Field Type Default Editable Description
fm_budget_line.budget_id,
fm_budget_line.account_code =
structur e.structur e_code)
AccountKey string nil Yes Structur e key URI for the account.
Structur e name = $Account. The account
must alr eady be associated with the
Model.
DB Info : structur e.structur e_code
(fm_budget_line.account_code =
structur e.structur e_code)
AccountPar entDescription string (50) n/a No Read only description of the par ent of the
account associated with this line.
DB Info : structur e_code.description
(fm_budget_line.account_code =
structur e.structur e_code,
structur e.structur e_code =
structur e.father_code)
Attributes ArrayOfLineAttributeDto nil Yes A collection of line attributes. The
attribute must alr eady be associated with
the account. See the LineAttributeDto .
DB Info : fm_budget_line_attrib
(fm_budget_line.line_id =
fm_budget_line_attrib.line_id)
CurrencyKey string USD No Currency key URI for the curr ency for this
line. All values in this line must be in this
currency .
DB Info : fm_budget_entry .currency_code
(fm_budget_line.line_id, =
fm_budget_entry .line_id)
Entries ArrayOfEntryDto nil Yes A collection of the entries for each period
of this line. See EntryDto .
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
75

Field Type Default Editable Description
DB Info : fm_budget_entry
(fm_budget_line.line_id =
fm_budget_entry .line_id)
LineId int n/a No Read only internal ID of this line.
DB Info : fm_budget_line.line_id
(fm_budget.budget_id =
fm_budget_line.budget_id)
Note string (4000) n/a Yes String containing information about the
financial plan line.1,4
The string must be pure text . For
example, HTML will cause an err or.
DB Info : fm_budget_line.note
Unit string nil Yes A single line can be br oken down into
three Unit types. The Unit type depend-
upon the type of account.1,2,3
DB Info : Note stor ed or r ead fr om
database.
Field Type Default Editable Description
AccountDescription string (50) n/a No Read only description of the account
associated with this line.
DB Info : structur e.description
(fm_budget.budget_id =
fm_budget_line.budget_id,
fm_budget_line.account_code =
structur e.structur e_code)
AccountKey string nil Yes Structur e key URI for the account.
Structur e name = $Account. The account
must alr eady be associated with the
Model.
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
76

Field Type Default Editable Description
DB Info : structur e.structur e_code
(fm_budget_line.account_code =
structur e.structur e_code)
AccountPar entDescription string (50) n/a No Read only description of the par ent of the
account associated with this line.
DB Info : structur e_code.description
(fm_budget_line.account_code =
structur e.structur e_code,
structur e.structur e_code =
structur e.father_code)
Attributes ArrayOfLineAttributeDto nil Yes A collection of line attributes. The
attribute must alr eady be associated with
the account. See the LineAttributeDto .
DB Info : fm_budget_line_attrib
(fm_budget_line.line_id =
fm_budget_line_attrib.line_id)
CurrencyKey string USD No Currency key URI for the curr ency for this
line. All values in this line must be in this
currency .
DB Info : fm_budget_entry .currency_code
(fm_budget_line.line_id, =
fm_budget_entry .line_id)
Entries ArrayOfEntryDto nil Yes A collection of the entries for each period
of this line. See EntryDto .
DB Info : fm_budget_entry
(fm_budget_line.line_id =
fm_budget_entry .line_id)
LineId int n/a No Read only internal ID of this line.
DB Info : fm_budget_line.line_id
(fm_budget.budget_id =
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
77

Field Type Default Editable Description
fm_budget_line.budget_id)
Unit string nil Yes A single line can be br oken down into
three Unit types. The Unit type depend-
upon the type of account.1,2,3
DB Info : Note stor ed or r ead fr om
database.
1A financial plan line is identified by its account and its attributes (if any). Each line can be br oken down into thr ee parts
which, in general, r epresent the number of units, the cost or income per unit and the total cost or income. A single
FinancialPlanDto represents only one these thr ee components. Which component the DTO represents is contr olled by
the Unit field in the DTO .Remarks
You ar e not r equir ed to pr ovide DTOs for all thr ee components. However you should be awar e of that, under some
circumstances, entering values for some unit types will cause the EntryDto.V alue field to be r ecalculated. See the DB
Info r emark for the V alue field of the Entry DTO for mor e information on r ecalculation of total cost and total income.
2Unit
An financial plan line under an account can have up to thr ee Unit types associated with it.
An income pr oducing account can have the following Unit types:
•Units – number of units
•Unit Price – income per unit
•Currency – total income
An expenditur e account (e.g. capitol, expense, depr eciation) can have the following Unit types:
•Units – number of units
•Unit Cost – cost per unit
•Currency – total cost
A Labor account can have the following Unit types:
•FTE – Full T ime Equivalent (1 FTE r epresents a person working full time)
•Hours – total hours worked
•Currency – total cost
Note : A variety of model, version, line, account, and attribute settings may pr event a financial plan, a line in the financial
plan or periods in the financial plan fr om being editable. An attempt to edit that which is not editable will generate an
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
78

error message in the OpenSuiteResult.
3Recalculations
Units, Unit Cost (or Unit Price), and Curr ency line items for an account ar e loaded in the or der in which they ar e
encounter ed. For example: If, when importing a line of data, the financial plan has a line item for Units, followed by a
line item for Unit Cost, and then a line item for Curr ency , the following actions ar e applied in or der:
•When the Units value is loaded, and if the Unit Cost exists in Planview , then the Curr ency will be r ecalculated.
•When the Unit Cost is loaded, and if the Units exists in Planview , then the Curr ency will be r ecalculated.
•When the Curr ency line item is loaded no change will be made to either the Unit Cost or Units line items for the
period.
•To prevent unwanted r ecalculation, users should r emove the unnecessary r ows fr om the input. T o prevent the
Currency value fr om being r ecalculated, the Curr ency line item should be added after the line items for Units and or
Unit Cost.
FTE, Hours, and Curr ency line items for an account ar e loaded in the or der in which they ar e encounter ed. For example:
If, when importing a line of data, the financial plan has a line item for FTEs, followed by a line item for Hours, and then a
line item for Curr ency , the following actions ar e applied in or der:
•When the FTE value is loaded, the Hours and Curr ency ar e recalculated (if these line item exists in the plan).
•When the Hours ar e loaded, overwriting the FTEs and Curr ency (if FTEs and Curr ency exist in the plan).
•When the Curr ency is loaded no change will be made to either the Unit Cost or Units line items for the period.
To prevent unwanted r ecalculation, users should r emove the unnecessary r ows fr om the input. T o avoid the Curr ency
field being overwritten, the Curr ency field should be pr ovided last.
4Note
•A line can be br oken down into thr ee parts1, but ther e is only one note.
•When r eading a line, the note will be r epeated on each of the parts.
•When upserting a line, the desir ed note must be on one or mor e of the line parts.
•A note cannot contain unencoded special characters that can be interpr eted as XML/HTML etc. This will cause a
deserialization err or an the financial plan will not be pr ocessed. The note will be interpr eted as plain text. Any
formatting characters will be tr eated as text.
•You cannot completely delete a note. Setting the note to "" or null will not update the note.
Complex T ype: LineAttributeDto
LineAttributeDto is a r epresentation of a line attribute for use within the interface IFinancialPlanService2 for the Financial
Plan web service.
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
79

Content Model
Contains elements as defined in the following table.
Field Type Default Editable Description
AltStructur eKey string nil Yes Structur e key URI for a line's account
attribute.
DB Info :
fm_budget_line_attrib.line_attrib_value
AltStrucutur eDescription string (10) n/a No Read only description of the attribute.
DB Info : structur e.description
(fm_budget_line_attrib.line_attrib_value =
structur e.structur e_code)
Remarks
Line attributes ar e alternate structur es that help classify financial data. Befor e you can use a line attribute with this web
service, you need to define (via the Planview Enterprise One UI) which attributes can be used with which accounts to
describe lines, as well as such things as whether an attribute is optional or r equir ed.
IFinancialPlanService2 © 2025 Planview , Inc.
Planview Confidential | All Rights Reserved
80
