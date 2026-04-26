# Test Cases

Use this checklist to verify the project in the browser.

## Environment

- Backend running at `http://localhost:8000`
- Frontend running at `http://localhost:5173`
- Groq API key configured if you want live NLP responses
- A sample submission file available for upload

## Quick Pass Criteria

A case passes when:
- the action completes without a crash
- the UI updates or API responds as expected
- no unexpected error message appears

## Browser Checklist

| ID | Area | Test | Expected Result |
|---|---|---|---|
| TC-01 | App Load | Open the frontend | Page loads, header and mode toggle are visible, default mode is Feedback Generator |
| TC-02 | Mode Switch | Switch to Chatbot and back | Visible panel changes correctly with no layout breakage |
| TC-03 | Upload | Upload a valid `.txt`, `.pdf`, or `.docx` file | Upload succeeds and file status updates |
| TC-04 | Upload Validation | Click Upload with no file selected | Upload does not proceed and a clear validation state appears |
| TC-05 | Rubric Builder | Add a rubric criterion | Criterion appears in the rubric list |
| TC-06 | Rubric Validation | Leave required rubric fields blank and click Add Criterion | Criterion is not added |
| TC-07 | Feedback Generation | Upload a file, add rubric criteria, and click Generate Feedback | Loading appears, then a full feedback report renders |
| TC-08 | Feedback Validation | Try generating feedback without required inputs | A clear validation message is shown |
| TC-09 | Chatbot Start | Attach a file and ask the first question | User message appears and assistant returns a contextual response |
| TC-10 | Grammar Check | Ask for grammatical errors in the uploaded document | Assistant returns specific grammar findings, not a generic placeholder |
| TC-11 | Follow-up Memory | Ask a second question in the same session without re-uploading | Same session is reused and the answer uses document/session context |
| TC-12 | Prior Context | Ask a follow-up that refers to the previous answer | Assistant responds using prior context correctly |
| TC-13 | Session Stability | Send several messages in one chat session | Session ID stays the same and messages remain in the chat log |
| TC-14 | Bridge JSON | Trigger the chatbot through the UI | Backend returns JSON with session_id, assistant_message, intent, planned_tools, executed_steps, and artifacts |
| TC-15 | Missing Context | Ask the chatbot to analyze without upload or raw text | The app returns a clear error or guided message |
| TC-16 | Invalid File Type | Upload an unsupported file type | The app rejects it or shows a clear backend error |
| TC-17 | Report Rendering | Generate a full feedback report | Score cards and sections render cleanly and are readable |
| TC-18 | Responsive Layout | Resize the browser to a narrow width | Controls stack cleanly and the UI stays usable |
| TC-19 | Health Check | Visit `http://localhost:8000/health` | Response is JSON: `{ "status": "ok" }` |

## Chatbot Prompt Samples

Use these prompts in the chatbot section after uploading a document.

### Grammar Check
- `Find grammatical errors in the uploaded document.`
- `List all grammar mistakes and explain each one.`
- `Show me the top 3 grammar issues in simple language.`

### Writing Quality and Clarity
- `Summarize the main idea of this submission.`
- `Explain whether the writing is clear and easy to follow.`
- `What are the biggest clarity problems in this text?`

### Flow and Coherence
- `Check the flow and coherence of the document.`
- `Tell me if the paragraphs connect well.`
- `Where does the argument lose logical flow?`

### Improvement Suggestions
- `Suggest improvements to make the writing more professional.`
- `Give me practical ways to improve this draft.`
- `What should the student revise first?`

### Rubric-Based Feedback
- `Give feedback based on the rubric and uploaded file.`
- `Score this submission against the rubric.`
- `Which rubric criteria need the most improvement?`

### Follow-up Questions
- `Can you explain the first issue in more detail?`
- `What is the most important fix from the previous answer?`
- `Based on the last response, what should be improved next?`

## Notes

- If Groq is not configured, NLP/chat responses may be limited or fall back.
- The most important checks are upload, feedback generation, chatbot analysis, and follow-up memory continuity.
