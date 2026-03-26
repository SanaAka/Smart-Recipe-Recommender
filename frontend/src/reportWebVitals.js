// Performance monitoring utility
export const reportWebVitals = (onPerfEntry) => {
  if (onPerfEntry && onPerfEntry instanceof Function) {
    import('web-vitals').then(({ getCLS, getFID, getFCP, getLCP, getTTFB }) => {
      getCLS(onPerfEntry);
      getFID(onPerfEntry);
      getFCP(onPerfEntry);
      getLCP(onPerfEntry);
      getTTFB(onPerfEntry);
    });
  }
};

// Log to console in development, send to analytics in production
export const logWebVitals = (metric) => {
  if (process.env.NODE_ENV === 'development') {
    console.log(metric);
  } else if (process.env.REACT_APP_ENABLE_ANALYTICS === 'true') {
    // Send to analytics service (Google Analytics, etc.)
    // window.gtag('event', metric.name, {
    //   value: Math.round(metric.name === 'CLS' ? metric.value * 1000 : metric.value),
    //   event_label: metric.id,
    //   non_interaction: true,
    // });
  }
};
