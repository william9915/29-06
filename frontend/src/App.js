import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const App = () => {
  const [darkMode, setDarkMode] = useState(false);
  const [query, setQuery] = useState("");
  const [author, setAuthor] = useState("");
  const [venue, setVenue] = useState("");
  const [yearFrom, setYearFrom] = useState("");
  const [yearTo, setYearTo] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchHistory, setSearchHistory] = useState([]);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [totalCount, setTotalCount] = useState(0);
  const [queryInfo, setQueryInfo] = useState(null);

  useEffect(() => {
    // Load theme preference
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme === "dark") {
      setDarkMode(true);
    }
    
    // Load search history
    loadSearchHistory();
  }, []);

  useEffect(() => {
    // Apply theme
    if (darkMode) {
      document.body.setAttribute("data-bs-theme", "dark");
      localStorage.setItem("theme", "dark");
    } else {
      document.body.removeAttribute("data-bs-theme");
      localStorage.setItem("theme", "light");
    }
  }, [darkMode]);

  const loadSearchHistory = async () => {
    try {
      const response = await axios.get(`${API}/search/history`);
      setSearchHistory(response.data);
    } catch (error) {
      console.error("Error loading search history:", error);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    try {
      const searchData = {
        query: query.trim(),
        author: author.trim() || null,
        venue: venue.trim() || null,
        year_from: yearFrom ? parseInt(yearFrom) : null,
        year_to: yearTo ? parseInt(yearTo) : null,
        limit: 20
      };

      const response = await axios.post(`${API}/search`, searchData);
      setSearchResults(response.data.papers);
      setTotalCount(response.data.total_count);
      setQueryInfo(response.data.query_info);
      loadSearchHistory(); // Refresh history
    } catch (error) {
      console.error("Search error:", error);
      alert("Search failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const clearHistory = async () => {
    try {
      await axios.delete(`${API}/search/history`);
      setSearchHistory([]);
      // Force refresh of search history to ensure UI is updated
      await loadSearchHistory();
    } catch (error) {
      console.error("Error clearing history:", error);
    }
  };

  const formatAuthors = (authors) => {
    if (!authors || authors.length === 0) return "Unknown authors";
    if (authors.length === 1) return authors[0];
    if (authors.length === 2) return authors.join(" and ");
    return `${authors.slice(0, 2).join(", ")} et al.`;
  };

  const truncateAbstract = (abstract, maxLength = 300) => {
    if (!abstract || abstract.length <= maxLength) return abstract;
    return abstract.substring(0, maxLength) + "...";
  };

  return (
    <div className={`app ${darkMode ? "dark-theme" : ""}`}>
      {/* Navigation */}
      <nav className="navbar navbar-expand-lg bg-body-tertiary shadow-sm">
        <div className="container">
          <a className="navbar-brand fw-bold fs-4" href="#">
            <i className="bi bi-search me-2"></i>
            ScholarSearch
          </a>
          <div className="d-flex align-items-center">
            <div className="form-check form-switch me-3">
              <input
                className="form-check-input"
                type="checkbox"
                id="themeToggle"
                checked={darkMode}
                onChange={(e) => setDarkMode(e.target.checked)}
              />
              <label className="form-check-label" htmlFor="themeToggle">
                <i className={`bi ${darkMode ? "bi-moon-stars" : "bi-sun"}`}></i>
              </label>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="hero-section">
        <div className="container text-center py-5">
          <div className="row justify-content-center">
            <div className="col-lg-8">
              <h1 className="display-4 fw-bold mb-4">
                Discover Academic Research
              </h1>
              <p className="lead mb-5">
                Search millions of scientific papers from Semantic Scholar and CrossRef
              </p>
              
              {/* Search Form */}
              <form onSubmit={handleSearch} className="search-form">
                <div className="input-group input-group-lg mb-3">
                  <input
                    type="text"
                    className="form-control"
                    placeholder="Search for papers, authors, or topics..."
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    required
                  />
                  <button 
                    className="btn btn-primary px-4" 
                    type="submit"
                    disabled={loading}
                  >
                    {loading ? (
                      <span className="spinner-border spinner-border-sm me-2" />
                    ) : (
                      <i className="bi bi-search me-2"></i>
                    )}
                    Search
                  </button>
                </div>
                
                {/* Advanced Search Toggle */}
                <div className="text-center mb-3">
                  <button
                    type="button"
                    className="btn btn-link"
                    onClick={() => setShowAdvanced(!showAdvanced)}
                  >
                    <i className={`bi ${showAdvanced ? "bi-chevron-up" : "bi-chevron-down"} me-1`}></i>
                    Advanced Search
                  </button>
                </div>
                
                {/* Advanced Search Fields */}
                {showAdvanced && (
                  <div className="row g-3 mb-3">
                    <div className="col-md-6">
                      <input
                        type="text"
                        className="form-control"
                        placeholder="Author name"
                        value={author}
                        onChange={(e) => setAuthor(e.target.value)}
                      />
                    </div>
                    <div className="col-md-6">
                      <input
                        type="text"
                        className="form-control"
                        placeholder="Venue/Journal"
                        value={venue}
                        onChange={(e) => setVenue(e.target.value)}
                      />
                    </div>
                    <div className="col-md-6">
                      <input
                        type="number"
                        className="form-control"
                        placeholder="From year"
                        value={yearFrom}
                        onChange={(e) => setYearFrom(e.target.value)}
                        min="1900"
                        max="2025"
                      />
                    </div>
                    <div className="col-md-6">
                      <input
                        type="number"
                        className="form-control"
                        placeholder="To year"
                        value={yearTo}
                        onChange={(e) => setYearTo(e.target.value)}
                        min="1900"
                        max="2025"
                      />
                    </div>
                  </div>
                )}
              </form>
            </div>
          </div>
        </div>
      </div>

      <div className="container my-5">
        <div className="row">
          {/* Main Content */}
          <div className="col-lg-8">
            {/* Search Results */}
            {queryInfo && (
              <div className="mb-4">
                <h5>
                  Search Results 
                  <span className="text-muted ms-2">({totalCount} papers found)</span>
                </h5>
                <p className="text-muted mb-3">
                  Query: "{queryInfo.query}"
                  {queryInfo.author && ` | Author: ${queryInfo.author}`}
                  {queryInfo.venue && ` | Venue: ${queryInfo.venue}`}
                  {queryInfo.year_range !== "any-any" && ` | Years: ${queryInfo.year_range}`}
                </p>
              </div>
            )}

            {searchResults.length > 0 && (
              <div className="search-results">
                {searchResults.map((paper, index) => (
                  <div key={paper.id} className="card mb-4 paper-card">
                    <div className="card-body">
                      <div className="d-flex justify-content-between align-items-start mb-2">
                        <h5 className="card-title mb-1">
                          {paper.url ? (
                            <a href={paper.url} target="_blank" rel="noopener noreferrer" className="text-decoration-none">
                              {paper.title}
                            </a>
                          ) : (
                            paper.title
                          )}
                        </h5>
                        <span className={`badge ${paper.source === 'Semantic Scholar' ? 'bg-primary' : 'bg-success'}`}>
                          {paper.source}
                        </span>
                      </div>
                      
                      <p className="card-text text-muted mb-2">
                        <i className="bi bi-people me-1"></i>
                        {formatAuthors(paper.authors)}
                        {paper.year && (
                          <>
                            <span className="mx-2">•</span>
                            <i className="bi bi-calendar me-1"></i>
                            {paper.year}
                          </>
                        )}
                        {paper.venue && (
                          <>
                            <span className="mx-2">•</span>
                            <i className="bi bi-journal me-1"></i>
                            {paper.venue}
                          </>
                        )}
                      </p>
                      
                      {paper.abstract && (
                        <p className="card-text mb-3">
                          {truncateAbstract(paper.abstract)}
                        </p>
                      )}
                      
                      <div className="d-flex justify-content-between align-items-center">
                        <div>
                          {paper.citation_count > 0 && (
                            <span className="badge bg-secondary me-2">
                              <i className="bi bi-quote me-1"></i>
                              {paper.citation_count} citations
                            </span>
                          )}
                          {paper.doi && (
                            <span className="badge bg-info text-dark">
                              DOI: {paper.doi}
                            </span>
                          )}
                        </div>
                        <div>
                          {paper.pdf_url && (
                            <a 
                              href={paper.pdf_url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="btn btn-outline-primary btn-sm me-2"
                            >
                              <i className="bi bi-file-pdf me-1"></i>
                              PDF
                            </a>
                          )}
                          {paper.url && (
                            <a 
                              href={paper.url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="btn btn-outline-secondary btn-sm"
                            >
                              <i className="bi bi-link-45deg me-1"></i>
                              View
                            </a>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {searchResults.length === 0 && !loading && queryInfo && (
              <div className="text-center py-5">
                <i className="bi bi-search display-1 text-muted"></i>
                <h4 className="mt-3">No papers found</h4>
                <p className="text-muted">Try adjusting your search terms or filters</p>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="col-lg-4">
            <div className="card">
              <div className="card-header d-flex justify-content-between align-items-center">
                <h6 className="mb-0">
                  <i className="bi bi-clock-history me-2"></i>
                  Recent Searches
                </h6>
                {searchHistory.length > 0 && (
                  <button 
                    className="btn btn-outline-danger btn-sm"
                    onClick={clearHistory}
                  >
                    Clear
                  </button>
                )}
              </div>
              <div className="card-body">
                {searchHistory.length > 0 ? (
                  <div className="list-group list-group-flush">
                    {searchHistory.slice(0, 10).map((item, index) => (
                      <div key={item.id} className="list-group-item px-0 py-2 border-0">
                        <button
                          className="btn btn-link p-0 text-start text-decoration-none"
                          onClick={() => setQuery(item.query)}
                        >
                          <div className="fw-medium">{item.query}</div>
                          <small className="text-muted">
                            {item.result_count} results • {new Date(item.timestamp).toLocaleDateString()}
                          </small>
                        </button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-muted mb-0">No recent searches</p>
                )}
              </div>
            </div>

            {/* Info Card */}
            <div className="card mt-4">
              <div className="card-header">
                <h6 className="mb-0">
                  <i className="bi bi-info-circle me-2"></i>
                  About ScholarSearch
                </h6>
              </div>
              <div className="card-body">
                <p className="small mb-2">
                  This academic search engine queries multiple sources:
                </p>
                <ul className="small mb-3">
                  <li><strong>Semantic Scholar</strong> - AI-powered academic search</li>
                  <li><strong>CrossRef</strong> - Comprehensive metadata database</li>
                </ul>
                <div className="d-flex justify-content-between text-muted small">
                  <span>Sources: 2</span>
                  <span>Papers: Millions</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-body-tertiary py-4 mt-5">
        <div className="container text-center">
          <p className="text-muted mb-0">
            Built with <i className="bi bi-heart-fill text-danger"></i> for academic research
          </p>
        </div>
      </footer>
    </div>
  );
};

export default App;