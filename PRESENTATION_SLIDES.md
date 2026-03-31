Smart Recipe Recommender — Presentation Deck

---

# Slide 1: Title
**Smart Recipe Recommender**  
AI-powered, end-to-end recipe discovery platform

Tech stack: React (frontend) · Flask + Python (backend/ML) · MySQL · Docker · JWT

---

# Slide 2: Agenda
- Introduction
- Literature Review
- Methodology
- Results
- Discussion
- Conclusion

---

# Slide 3: Introduction
- Problem: Choosing what to cook with limited ingredients and dietary constraints is slow; manual search wastes time and food.
- Solution: Personalized recipe recommendations based on ingredients, dietary and cuisine preferences, and difficulty/time constraints.
- Scope: Full-stack web app, 2M+ recipes, secured with JWT, rate limiting, and validation; 8 standout backend features (scaling, grocery list, expiry tracker, nutrition goals, difficulty predictor, wine pairing, leftover transformer, cooking coach).

---

# Slide 4: Literature Review
- Content-based filtering (TF-IDF + cosine similarity) for ingredient/text similarity.
- Collaborative filtering and hybrid recommenders noted as future expansion to address cold-start and preference learning.
- Evaluation metrics commonly used: Precision@K, Recall@K, F1@K, NDCG, MAP, coverage/diversity.
- Dataset references: Food.com / Kaggle large-scale recipe datasets; prior work on IR-based recommenders (Adomavicius & Tuzhilin, 2005; Ricci et al., 2015).

---

# Slide 5: Methodology (Architecture)
- React SPA consumes Flask REST API; JWT-secured endpoints with rate limiting and Pydantic validation.
- ML service: content-based model (TF-IDF vectors + cosine similarity) with multi-factor scoring (ingredients, dietary, cuisine).
- Data: MySQL with normalized recipe, ingredients, nutrition, steps, tags, plus 7 new tables for standout features.
- Logging & Ops: Structured JSON logging; CI/CD via GitHub Actions; Docker-compose for local.

System sketch (text):
User → React → Flask API → (ML model · MySQL) → Response

---

# Slide 6: Methodology (Pipelines)
1) Data ingestion & cleaning → tokenize ingredients, build vocabulary.  
2) Feature extraction → TF-IDF weighting; cosine similarity for ranking.  
3) Scoring → Ingredient match + dietary/cuisine filters + time/difficulty signals.  
4) Standout feature services → recipe scaling parser, grocery categorizer, expiry status calculator, nutrition goal tracker, difficulty scorer, wine pairing rules, leftover matcher, cooking coach sessions.  
5) Security & quality → JWT auth, rate limiting, validation schemas, structured error handling, logging.

---

# Slide 7: Results
- Quality uplift: overall score 4.7 → 7.8 (+66%); security 3 → 8; testing 2 → 8; CI/CD from 0 → 8 (see Improvements Summary).
- Backend complete: 25+ new endpoints; 7 new tables; blueprint integrated in app_v2.py; env constants unchanged.
- Performance highlights: search and recommend endpoints optimized with indexing and caching (target sub-200ms typical loads); scalable via connection pooling.
- Production-readiness: JWT + rate limiting, structured logging, pytest coverage, GitHub Actions pipelines, dockerized setup.

---

# Slide 8: Discussion
- Strengths: Comprehensive security posture; rich feature set (8 standout modules); documented APIs; modular Flask blueprints; strong testing and CI/CD.
- Limitations: Frontend coverage of standout features still in progress; cold-start for brand-new users without history; primarily content-based model (collaborative filtering pending); dependency on dataset quality.
- Next steps: Finish UI for standout features; add collaborative filtering / hybrid model; user study + A/B tests; extend monitoring (APM) and caching layer; mobile responsiveness.

---

# Slide 9: Conclusion
- Built an end-to-end, secure, ML-driven recipe recommender with measurable quality gains and 8 differentiating backend capabilities.
- Ready for stakeholder demo and small-to-medium production trial after frontend completes standout features and final integration testing.
- Future impact: reduce food waste (expiry tracker, leftover transformer), improve adherence to nutrition goals, and speed meal decisions.

---

# Slide 10: References
- Adomavicius, G., & Tuzhilin, A. (2005). Toward the next generation of recommender systems.
- Ricci, F., Rokach, L., & Shapira, B. (2015). Recommender Systems Handbook.
- Manning, C. D., Raghavan, P., & Schütze, H. (2008). Introduction to Information Retrieval.
- Food.com Recipes Dataset (Kaggle).
- Project docs: README.md, BACKEND_IMPLEMENTATION_SUMMARY.md, IMPROVEMENTS_SUMMARY.md, STANDOUT_FEATURES_GUIDE.md.