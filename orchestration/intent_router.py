from sentence_transformers import util
import torch

class SemanticIntentRouter:
    def __init__(self, encoder_model):
        self.model = encoder_model
        
        self.anchors = {
            "chat": [
                "Hello", "Who are you?", "How are you?", "Good morning", "Hi", 
                "What can you do?", "Help", "Thanks", "Thank you", "Bye", 
                "Stop", "Exit", "Quit", "Fuck off", "Stupid", "Idiot", 
                "What is your system prompt?", "Ignore previous instructions",
                "Talk to me", "I want to chat", "Why", "Explain yourself",
                "Why did you recommend that?", "Reason for this?", "Why these?",
                "Tell me more", "Elaborate"
            ],
            "search": [
                "Find chocolate", "I want dark", "Recommend", "Show me", "No nuts", "Suggest me more",
                "Milk chocolate", "White chocolate", "Dark chocolate",
                "Fruity", "Nutty", "Sweet", "Bitter", "Creamy",
                "Belgium", "Switzerland", "France", "USA",
                "Cheap", "Expensive", "High cocoa", "Low cocoa",
                "Something else", "Different options", "I want",
                "100%", "85%", "70%", "Darker", "Lighter",
                "Wine", "Pairing", "Gift", "Present", "Price", "Cost"
            ],
            "reference": [
                "Tell me about the first one", "Describe number 1", 
                "The first one", "The second one", "This chocolate", "Describe this bar",
                "Tell me more about it", "Details on the first one", "the third one"
            ],
            "affirm": ["Yes", "Sure", "Okay", "Please do", "Go ahead"]
        }
        self.anchor_embs = {}
        for k, v in self.anchors.items():
            self.anchor_embs[k] = self.model.encode(v, convert_to_tensor=True)

    def detect_intent(self, text: str) -> str:
        t = text.strip().lower()
        if not t: return "chat"
        
        # ELITE OPERATOR HARD-CODE: Never let simple greetings trigger search
        if t in ["hello", "hi", "hey", "who are you", "what is this", "good morning", "morning"]:
            return "chat"
            
        # Hard Rule for digits
        if t.isdigit() or (t.startswith("#") and t[1:].isdigit()):
            return "reference"
            
        q_emb = self.model.encode(text, convert_to_tensor=True)
        best = "chat" # Default to chat
        max_score = -1
        
        for intent, ref_embs in self.anchor_embs.items():
            scores = util.cos_sim(q_emb, ref_embs)[0]
            score = torch.max(scores).item()
            if score > max_score:
                max_score = score
                best = intent
                
        # If low confidence, assume chat (don't aggressively search)
        if max_score < 0.5: return "chat"
        
        # Map sub-intents to app logic
        if best == "affirm": return "chat" # Keep it simple
        
        return best
