# DraftGenie Visual Workflows & User Journey Maps

**Version:** 1.0  
**Last Updated:** 2025-10-16  
**Companion to:** `ui_ux_design_specification.md`

---

## Table of Contents

1. [User Journey Maps](#1-user-journey-maps)
2. [Detailed Workflow Diagrams](#2-detailed-workflow-diagrams)
3. [Screen Flow Diagrams](#3-screen-flow-diagrams)
4. [State Diagrams](#4-state-diagrams)
5. [Error Flow Diagrams](#5-error-flow-diagrams)

---

## 1. User Journey Maps

### 1.1 Administrator Journey: Speaker Onboarding

```mermaid
journey
    title Administrator Onboarding a New Speaker (SSA)
    section Discovery
      Navigate to Speakers: 5: Admin
      Click "Add Speaker": 5: Admin
    section Input
      Fill speaker form: 4: Admin
      Select initial bucket: 4: Admin
      Add metadata: 3: Admin
    section Validation
      System validates: 5: System
      Check for duplicates: 5: System
    section Confirmation
      Review summary: 4: Admin
      Click "Create": 5: Admin
    section Processing
      Speaker created: 5: System
      Drafts ingesting: 4: System
      Success notification: 5: Admin
    section Follow-up
      View speaker profile: 5: Admin
      Monitor draft ingestion: 4: Admin
```

### 1.2 Quality Analyst Journey: Evaluation Review

```mermaid
journey
    title Quality Analyst Reviewing Evaluations
    section Access
      Login to dashboard: 5: Analyst
      Navigate to Evaluations: 5: Analyst
    section Discovery
      View pending evaluations: 4: Analyst
      Filter by speaker/date: 4: Analyst
    section Analysis
      Open evaluation detail: 5: Analyst
      Compare DFN vs IFN: 5: Analyst
      Review quality metrics: 4: Analyst
    section Decision
      Analyze bucket recommendation: 4: Analyst
      Consider speaker history: 3: Analyst
    section Action
      Approve bucket change: 5: Analyst
      Add review notes: 3: Analyst
      Confirm decision: 5: Analyst
    section Completion
      Success notification: 5: System
      Speaker bucket updated: 5: System
```

### 1.3 Speaker Journey: Viewing Performance

```mermaid
journey
    title Medical Professional Viewing Their Performance
    section Access
      Login to portal: 5: Speaker
      View personal dashboard: 5: Speaker
    section Overview
      See quality metrics: 4: Speaker
      View current bucket: 4: Speaker
      Check improvement trend: 5: Speaker
    section Details
      Browse my drafts: 4: Speaker
      View correction patterns: 3: Speaker
      See final notes (DFN): 5: Speaker
    section Insights
      Understand corrections: 4: Speaker
      Identify improvement areas: 4: Speaker
    section Satisfaction
      Feel confident in system: 5: Speaker
```

---

## 2. Detailed Workflow Diagrams

### 2.1 Complete Speaker Onboarding Workflow (SSA)

```mermaid
flowchart TD
    Start([User clicks 'Add Speaker']) --> Form[Display Speaker Form]
    Form --> Input[User enters speaker details]
    Input --> Validate{Client-side validation}
    
    Validate -->|Invalid| ShowError[Show inline errors]
    ShowError --> Input
    
    Validate -->|Valid| Submit[User clicks 'Create']
    Submit --> API[POST /api/v1/speakers]
    
    API --> CheckResponse{API Response}
    
    CheckResponse -->|201 Created| Success[Show success toast]
    CheckResponse -->|409 Conflict| Duplicate[Show 'Duplicate External ID' error]
    CheckResponse -->|400 Bad Request| ValidationError[Show validation errors]
    CheckResponse -->|500 Server Error| ServerError[Show 'Server error, try again']
    
    Duplicate --> Input
    ValidationError --> Input
    ServerError --> Retry{User retries?}
    Retry -->|Yes| Submit
    Retry -->|No| End([End])
    
    Success --> Redirect[Redirect to speaker profile]
    Redirect --> Background[Background: Ingest drafts]
    Background --> ShowStatus[Show 'Ingesting drafts...' status]
    ShowStatus --> Poll[Poll draft ingestion status]
    
    Poll --> CheckIngestion{Ingestion complete?}
    CheckIngestion -->|No| Wait[Wait 2 seconds]
    Wait --> Poll
    CheckIngestion -->|Yes| Complete[Show 'Drafts ingested' notification]
    Complete --> End
    
    style Success fill:#4CAF50,color:#fff
    style Duplicate fill:#F44336,color:#fff
    style ValidationError fill:#FF9800,color:#fff
    style ServerError fill:#F44336,color:#fff
```

### 2.2 Batch Speaker Addition Workflow (BSA)

```mermaid
flowchart TD
    Start([User clicks 'Bulk Import']) --> Upload[Show upload wizard]
    Upload --> Choose{Upload method}
    
    Choose -->|File| FileUpload[Upload CSV/Excel]
    Choose -->|Paste| PasteData[Paste tab-separated data]
    
    FileUpload --> Parse[Parse file]
    PasteData --> Parse
    
    Parse --> Validate[Validate all entries]
    Validate --> Preview[Show preview table]
    Preview --> Review{User reviews}
    
    Review -->|Fix errors| EditInline[Edit invalid rows inline]
    EditInline --> Validate
    
    Review -->|Cancel| End([End])
    
    Review -->|Confirm| Summary[Show summary: X valid, Y errors]
    Summary --> Proceed{Proceed?}
    
    Proceed -->|No| End
    Proceed -->|Yes| Process[Start processing]
    
    Process --> Loop[For each valid speaker]
    Loop --> CreateAPI[POST /api/v1/speakers]
    CreateAPI --> UpdateProgress[Update progress bar]
    UpdateProgress --> CheckMore{More speakers?}
    
    CheckMore -->|Yes| Loop
    CheckMore -->|No| Results[Show results summary]
    
    Results --> Report[Display success/error counts]
    Report --> Download[Offer error report download]
    Download --> ViewList[Link to speaker list]
    ViewList --> End
    
    style Process fill:#2196F3,color:#fff
    style Results fill:#4CAF50,color:#fff
```

### 2.3 DFN Generation Workflow

```mermaid
flowchart TD
    Start([User clicks 'Generate DFN']) --> CheckSpeaker{Speaker selected?}
    
    CheckSpeaker -->|No| SelectSpeaker[Show speaker selection]
    SelectSpeaker --> CheckSpeaker
    
    CheckSpeaker -->|Yes| ShowModal[Show generation modal]
    ShowModal --> EnterPrompt[User enters prompt optional]
    EnterPrompt --> ConfigOptions[Configure advanced options]
    ConfigOptions --> ClickGenerate[User clicks 'Generate']
    
    ClickGenerate --> ShowLoading[Show loading state]
    ShowLoading --> Step1[Step 1: Validating speaker ✓]
    Step1 --> API1[GET /api/v1/speakers/id]
    
    API1 --> CheckSpeakerExists{Speaker exists?}
    CheckSpeakerExists -->|No| Error404[Show 'Speaker not found']
    Error404 --> End([End])
    
    CheckSpeakerExists -->|Yes| Step2[Step 2: Retrieving context ✓]
    Step2 --> API2[GET /api/v1/drafts/speaker/id]
    
    API2 --> CheckDrafts{Has drafts?}
    CheckDrafts -->|No| ErrorNoDrafts[Show 'No drafts available']
    ErrorNoDrafts --> SuggestIngest[Suggest 'Ingest Drafts']
    SuggestIngest --> End
    
    CheckDrafts -->|Yes| Step3[Step 3: Generating with AI... ⏳]
    Step3 --> API3[POST /api/v1/workflow/generate-dfn]
    
    API3 --> Wait[Wait 10-30 seconds]
    Wait --> CheckResponse{Response?}
    
    CheckResponse -->|Timeout| ErrorTimeout[Show 'Generation timeout']
    ErrorTimeout --> Retry{Retry?}
    Retry -->|Yes| API3
    Retry -->|No| End
    
    CheckResponse -->|Error| ErrorGeneration[Show error message]
    ErrorGeneration --> Retry
    
    CheckResponse -->|Success| ShowDFN[Display generated DFN]
    ShowDFN --> ShowMetrics[Show quality metrics]
    ShowMetrics --> Actions{User action}
    
    Actions -->|Accept| SaveDFN[Save DFN to database]
    Actions -->|Regenerate| ClickGenerate
    Actions -->|Edit| EditDFN[Open editor]
    Actions -->|Cancel| End
    
    SaveDFN --> Success[Show success notification]
    Success --> TriggerEval[Trigger evaluation automatically]
    TriggerEval --> End
    
    EditDFN --> SaveEdited[Save edited version]
    SaveEdited --> Success
    
    style ShowDFN fill:#4CAF50,color:#fff
    style ErrorTimeout fill:#F44336,color:#fff
    style ErrorGeneration fill:#F44336,color:#fff
    style Success fill:#4CAF50,color:#fff
```

### 2.4 Evaluation & Bucket Reassignment Workflow

```mermaid
flowchart TD
    Start([Evaluation triggered]) --> Fetch[Fetch DFN and IFN]
    Fetch --> Compare[Compare texts]
    Compare --> CalcSER[Calculate SER]
    CalcSER --> CalcWER[Calculate WER]
    CalcWER --> CalcSim[Calculate Similarity]
    CalcSim --> CalcQuality[Calculate Quality Score]
    
    CalcQuality --> DetermineBucket[Determine recommended bucket]
    DetermineBucket --> SaveEval[Save evaluation to database]
    SaveEval --> Notify[Notify Quality Analyst]
    
    Notify --> AnalystReview[Analyst reviews evaluation]
    AnalystReview --> ViewComparison[View DFN vs IFN comparison]
    ViewComparison --> ViewMetrics[View quality metrics]
    ViewMetrics --> Decision{Analyst decision}
    
    Decision -->|Approve| ApproveBucket[Approve bucket change]
    Decision -->|Reject| RejectBucket[Reject recommendation]
    Decision -->|Defer| DeferDecision[Defer for later]
    
    ApproveBucket --> UpdateAPI[PUT /api/v1/speakers/id/bucket]
    UpdateAPI --> UpdateSuccess{Update successful?}
    
    UpdateSuccess -->|Yes| UpdateBadge[Update bucket badge in UI]
    UpdateSuccess -->|No| ShowError[Show error message]
    
    UpdateBadge --> LogChange[Log bucket change in audit]
    LogChange --> NotifySpeaker[Notify speaker optional]
    NotifySpeaker --> End([End])
    
    RejectBucket --> LogRejection[Log rejection reason]
    LogRejection --> End
    
    DeferDecision --> MarkPending[Mark as pending]
    MarkPending --> End
    
    ShowError --> RetryUpdate{Retry?}
    RetryUpdate -->|Yes| UpdateAPI
    RetryUpdate -->|No| End
    
    style UpdateBadge fill:#4CAF50,color:#fff
    style ShowError fill:#F44336,color:#fff
```

---

## 3. Screen Flow Diagrams

### 3.1 Main Navigation Flow

```mermaid
flowchart LR
    Login[Login Screen] --> Dashboard[Dashboard]
    
    Dashboard --> Speakers[Speakers List]
    Dashboard --> Evaluations[Evaluations]
    Dashboard --> Reports[Reports]
    Dashboard --> Settings[Settings]
    
    Speakers --> SpeakerProfile[Speaker Profile]
    SpeakerProfile --> Drafts[Drafts Tab]
    SpeakerProfile --> EvalTab[Evaluations Tab]
    SpeakerProfile --> SettingsTab[Settings Tab]
    
    Speakers --> AddSpeaker[Add Speaker Form]
    Speakers --> BulkImport[Bulk Import Wizard]
    
    SpeakerProfile --> GenerateDFN[Generate DFN Modal]
    
    Evaluations --> EvalDetail[Evaluation Detail]
    EvalDetail --> Comparison[DFN vs IFN Comparison]
    
    style Dashboard fill:#2196F3,color:#fff
    style SpeakerProfile fill:#4CAF50,color:#fff
```

### 3.2 Speaker Management Flow

```mermaid
stateDiagram-v2
    [*] --> SpeakersList
    
    SpeakersList --> AddSpeaker: Click "Add Speaker"
    SpeakersList --> BulkImport: Click "Bulk Import"
    SpeakersList --> SpeakerProfile: Click speaker name
    SpeakersList --> FilteredList: Apply filters
    
    FilteredList --> SpeakersList: Clear filters
    
    AddSpeaker --> SpeakersList: Cancel
    AddSpeaker --> SpeakerProfile: Success
    
    BulkImport --> SpeakersList: Cancel/Complete
    
    SpeakerProfile --> EditSpeaker: Click "Edit"
    SpeakerProfile --> GenerateDFN: Click "Generate DFN"
    SpeakerProfile --> ViewDrafts: Click "Drafts" tab
    SpeakerProfile --> ViewEvaluations: Click "Evaluations" tab
    
    EditSpeaker --> SpeakerProfile: Save/Cancel
    GenerateDFN --> SpeakerProfile: Close modal
    ViewDrafts --> DraftDetail: Click draft
    ViewEvaluations --> EvaluationDetail: Click evaluation
    
    DraftDetail --> ViewDrafts: Back
    EvaluationDetail --> ViewEvaluations: Back
    
    SpeakerProfile --> SpeakersList: Back to list
```

---

## 4. State Diagrams

### 4.1 Speaker State Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Creating: User submits form
    Creating --> Active: Creation successful
    Creating --> [*]: Creation failed
    
    Active --> Inactive: Admin deactivates
    Active --> Pending: Awaiting verification
    Active --> Archived: Admin archives
    
    Inactive --> Active: Admin reactivates
    Pending --> Active: Verification complete
    Pending --> Inactive: Verification failed
    
    Archived --> [*]: Soft deleted
    
    note right of Active
        Speaker can have drafts ingested
        DFN can be generated
        Evaluations can be performed
    end note
    
    note right of Inactive
        No new operations allowed
        Historical data preserved
    end note
```

### 4.2 Draft Processing State

```mermaid
stateDiagram-v2
    [*] --> Ingested: Draft ingested from InstaNote
    
    Ingested --> Processing: Vector generation started
    Processing --> Processed: Vector generated successfully
    Processing --> Failed: Vector generation failed
    
    Failed --> Processing: Retry
    Failed --> [*]: Permanent failure
    
    Processed --> InUse: Used in DFN generation
    
    InUse --> [*]: Draft lifecycle complete
    
    note right of Processed
        Draft ready for RAG
        Vector stored in Qdrant
        Can be used for DFN generation
    end note
```

### 4.3 Evaluation State

```mermaid
stateDiagram-v2
    [*] --> Triggered: DFN generated
    
    Triggered --> InProgress: Evaluation started
    InProgress --> Completed: Metrics calculated
    InProgress --> Failed: Calculation error
    
    Failed --> InProgress: Retry
    Failed --> [*]: Permanent failure
    
    Completed --> PendingReview: Awaiting analyst
    PendingReview --> Approved: Analyst approves
    PendingReview --> Rejected: Analyst rejects
    PendingReview --> Deferred: Analyst defers
    
    Approved --> BucketUpdated: Bucket changed
    BucketUpdated --> [*]
    
    Rejected --> [*]
    Deferred --> PendingReview: Analyst returns
    
    note right of Completed
        Quality metrics available
        Bucket recommendation made
        Ready for analyst review
    end note
```

---

## 5. Error Flow Diagrams

### 5.1 Authentication Error Flow

```mermaid
flowchart TD
    Start([User attempts action]) --> CheckAuth{Authenticated?}
    
    CheckAuth -->|Yes| CheckToken{Token valid?}
    CheckAuth -->|No| RedirectLogin[Redirect to login]
    
    CheckToken -->|Yes| AllowAction[Allow action]
    CheckToken -->|No| TryRefresh[Attempt token refresh]
    
    TryRefresh --> RefreshAPI[POST /auth/refresh]
    RefreshAPI --> RefreshSuccess{Refresh successful?}
    
    RefreshSuccess -->|Yes| UpdateToken[Update access token]
    RefreshSuccess -->|No| RedirectLogin
    
    UpdateToken --> RetryAction[Retry original action]
    RetryAction --> AllowAction
    
    RedirectLogin --> ShowLogin[Show login screen]
    ShowLogin --> UserLogin[User logs in]
    UserLogin --> LoginAPI[POST /auth/login]
    
    LoginAPI --> LoginSuccess{Login successful?}
    LoginSuccess -->|Yes| StoreTokens[Store tokens]
    LoginSuccess -->|No| ShowError[Show login error]
    
    StoreTokens --> AllowAction
    ShowError --> UserLogin
    
    AllowAction --> End([End])
    
    style AllowAction fill:#4CAF50,color:#fff
    style RedirectLogin fill:#FF9800,color:#fff
    style ShowError fill:#F44336,color:#fff
```

### 5.2 API Error Handling Flow

```mermaid
flowchart TD
    Start([API call initiated]) --> MakeRequest[Send HTTP request]
    MakeRequest --> WaitResponse[Wait for response]
    
    WaitResponse --> CheckStatus{HTTP Status}
    
    CheckStatus -->|200-299| Success[Parse response]
    CheckStatus -->|400| BadRequest[Show validation errors]
    CheckStatus -->|401| Unauthorized[Trigger auth flow]
    CheckStatus -->|403| Forbidden[Show 'Access denied']
    CheckStatus -->|404| NotFound[Show 'Not found']
    CheckStatus -->|409| Conflict[Show conflict message]
    CheckStatus -->|429| RateLimit[Show 'Too many requests']
    CheckStatus -->|500-599| ServerError[Show server error]
    CheckStatus -->|Timeout| Timeout[Show timeout error]
    CheckStatus -->|Network| NetworkError[Show network error]
    
    Success --> UpdateUI[Update UI with data]
    UpdateUI --> End([End])
    
    BadRequest --> ShowInline[Display inline errors]
    ShowInline --> End
    
    Unauthorized --> RefreshToken[Attempt token refresh]
    RefreshToken --> End
    
    Forbidden --> LogError[Log error]
    Forbidden --> ShowMessage[Show error message]
    ShowMessage --> End
    
    NotFound --> ShowMessage
    Conflict --> ShowMessage
    
    RateLimit --> WaitRetry[Wait before retry]
    WaitRetry --> RetryPrompt{Auto retry?}
    RetryPrompt -->|Yes| MakeRequest
    RetryPrompt -->|No| ShowMessage
    
    ServerError --> RetryPrompt
    Timeout --> RetryPrompt
    NetworkError --> RetryPrompt
    
    LogError --> End
    
    style Success fill:#4CAF50,color:#fff
    style BadRequest fill:#FF9800,color:#fff
    style ServerError fill:#F44336,color:#fff
    style Timeout fill:#F44336,color:#fff
```

---

## Usage Guidelines

### For Designers
- Use these diagrams as reference when creating mockups
- Ensure all states and transitions are represented in designs
- Consider error states and edge cases

### For Developers
- Implement state management based on state diagrams
- Follow error handling patterns from error flow diagrams
- Use workflow diagrams to understand business logic

### For QA/Testing
- Create test cases based on workflow diagrams
- Verify all state transitions work correctly
- Test error scenarios from error flow diagrams

---

**Document Version:** 1.0  
**Last Updated:** 2025-10-16  
**Related Documents:**
- `ui_ux_design_specification.md` - Main specification
- `FRONTEND_API_DOCUMENTATION.md` - API reference
- `system_architecture_and_implementation_plan.md` - System architecture

