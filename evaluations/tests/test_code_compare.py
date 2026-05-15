from __future__ import annotations

from agent_evaluations.code_compare import compare_code


def test_compare_code_matches_python_ast_semantics() -> None:
    left = 'def target(value):\n    """Doc."""\n    return value + 1\n'
    right = "def target(value):\n    return value + 1\n"

    result = compare_code("python", left, right)

    assert result.matched is True
    assert result.method == "python_ast"


def test_compare_code_matches_cpp_template_function() -> None:
    left = """
        template <typename T>
        inline auto ConvertToStorageValue(const T& t) {
            if constexpr (std::is_same_v<std::string_view, T> || std::is_same_v<std::string, T>) {
                return std::string_view{t};
            } else if constexpr (std::is_fundamental_v<T> || std::is_same_v<Int128, std::decay_t<T>>) {
                return std::string_view{reinterpret_cast<const char*>(&t), sizeof(T)};
            } else {
                static_assert(!std::is_same_v<T, T>, "Unknown type, which can't be stored in ItemView");
                return;
            }
        }
    """
    right = """
    template <typename T>
    inline auto ConvertToStorageValue(const T& t) {
        if constexpr (std::is_same_v<std::string_view, T> || std::is_same_v<std::string, T>) {
            return std::string_view{t};
        } else if constexpr (std::is_fundamental_v<T> || std::is_same_v<Int128, std::decay_t<T>>) {
            return std::string_view{reinterpret_cast<const char*>(&t), sizeof(T)};
        } else {
            static_assert(!std::is_same_v<T, T>, "Unknown type, which can't be stored in ItemView");
            return;
        }
    }
    """

    result = compare_code("cpp", left, right)

    assert result.matched is True
    assert result.method == "cpp_tree_sitter"


def test_compare_code_matches_java_method_with_indent_difference() -> None:
    left = """
        public void sMix(byte[] intensiveSalt, int bi, byte[] vArray, byte[] xyArray)
        {
            int xi = 0;
            int yi = 128 * resources;
            System.arraycopy(intensiveSalt, bi, xyArray, xi, 128 * resources);
        }
    """
    right = """
    public void sMix(byte[] intensiveSalt, int bi, byte[] vArray, byte[] xyArray)
    {
        int xi = 0;
        int yi = 128 * resources;
        System.arraycopy(intensiveSalt, bi, xyArray, xi, 128 * resources);
    }
    """

    result = compare_code("java", left, right)

    assert result.matched is True
    assert result.method == "java_tree_sitter"


def test_compare_code_matches_typescript_when_comment_is_omitted() -> None:
    left = """
      /* exported by axios */
    export default function isAxiosError(payload) {
      return utils.isObject(payload) && (payload.isAxiosError === true);
    }
    """
    right = """
    export default function isAxiosError(payload) {
      return utils.isObject(payload) && (payload.isAxiosError === true);
    }
    """

    result = compare_code("typescript", left, right)

    assert result.matched is True
    assert result.method == "typescript_tree_sitter"


def test_compare_code_matches_cpp_function_inside_namespace_wrapper() -> None:
    left = """
    namespace tags {
      static rgba get_color(color_value c, rgba fallback) {
        if (c.type == color_type::RESET) {
          return fallback;
        } else {
          return c.val;
        }
      }
    """
    right = """
    static rgba get_color(color_value c, rgba fallback) {
      if (c.type == color_type::RESET) {
        return fallback;
      } else {
        return c.val;
      }
    }
    """

    result = compare_code("cpp", left, right)

    assert result.matched is True


def test_compare_code_matches_rust_function_when_doc_comment_is_omitted() -> None:
    left = """
        /// Add a type to the request's `http::Extensions`.
        pub fn extension<T>(mut self, ext: T) -> Self
        where
            T: Send + Sync + 'static,
        {
            self.req.extensions_mut().insert(ext);
            self
        }
    """
    right = """
    pub fn extension<T>(mut self, ext: T) -> Self
    where
        T: Send + Sync + 'static,
    {
        self.req.extensions_mut().insert(ext);
        self
    }
    """

    result = compare_code("rust", left, right)

    assert result.matched is True
    assert result.method == "rust_tree_sitter"


def test_compare_code_rejects_wrong_go_function() -> None:
    left = """
    func newSnapshotCreateCommand() *cobra.Command {
        createCmd := &cobra.Command{
            Use:  "create INSTANCE",
            RunE: snapshotCreateAction,
        }
        return createCmd
    }
    """
    right = """
    func snapshotCreateAction(cmd *cobra.Command, args []string) error {
        return nil
    }
    """

    result = compare_code("go", left, right)

    assert result.matched is False
    assert result.method == "go_tree_sitter"


def test_compare_code_rejects_wrong_java_method() -> None:
    left = """
      @Nullable
      public ImmutableMap<String, String> getEnvironmentMap() {
        return environmentMap;
      }
    """
    right = """
    @Nullable
    public ImmutableMap<String, String> getEnvironment() {
      return environment;
    }
    """

    result = compare_code("java", left, right)

    assert result.matched is False