export default function(eleventyConfig) {
  eleventyConfig.addPassthroughCopy("public");
  eleventyConfig.addFilter("head", (values, count) =>
    count < 0 ? values.slice(count) : values.slice(0, count)
  );
  return {
    dir: {
      input: "content",
      includes: "../_includes",
      output: "_site"
    }
  };
}
