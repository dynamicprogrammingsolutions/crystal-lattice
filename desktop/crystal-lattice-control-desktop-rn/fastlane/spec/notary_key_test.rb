# frozen_string_literal: true

require "base64"
require "fastlane"
require "minitest/autorun"
require "tempfile"

Fastlane::Actions.load_default_actions

class MacNotaryKeyTest < Minitest::Test
  KEY_VARIABLES = %w[
    DESKTOP_APP_STORE_CONNECT_KEY_PATH
    DESKTOP_APP_STORE_CONNECT_KEY_CONTENT
    DESKTOP_APP_STORE_CONNECT_KEY_CONTENT_BASE64
  ].freeze

  def self.fastfile
    @fastfile ||= Fastlane::FastFile.new(
      File.expand_path("../Fastfile", __dir__),
    )
  end

  def setup
    @previous_values = KEY_VARIABLES.to_h { |name| [name, ENV[name]] }
    @fastfile = self.class.fastfile
  end

  def teardown
    @previous_values.each { |name, value| ENV[name] = value }
  end

  def test_local_key_path_returns_the_notarization_result
    Tempfile.create(["notary-path-test", ".p8"]) do |file|
      ENV["DESKTOP_APP_STORE_CONNECT_KEY_PATH"] = file.path
      ENV.delete("DESKTOP_APP_STORE_CONNECT_KEY_CONTENT")

      result = @fastfile.send(:with_notary_key) do |path|
        assert_equal file.path, path
        { "status" => "Accepted", "id" => "local-test" }
      end

      assert_equal "local-test", result.fetch("id")
    end
  end

  def test_inline_key_is_owner_only_and_removed_after_returning_result
    ENV.delete("DESKTOP_APP_STORE_CONNECT_KEY_PATH")
    ENV["DESKTOP_APP_STORE_CONNECT_KEY_CONTENT"] =
      Base64.strict_encode64("synthetic key bytes")
    ENV["DESKTOP_APP_STORE_CONNECT_KEY_CONTENT_BASE64"] = "true"
    temporary_path = nil

    result = @fastfile.send(:with_notary_key) do |path|
      temporary_path = path
      assert_equal "synthetic key bytes", File.binread(path)
      assert_equal 0o600, File.stat(path).mode & 0o777
      { "status" => "Accepted", "id" => "inline-test" }
    end

    assert_equal "inline-test", result.fetch("id")
    refute_path_exists temporary_path
  end
end