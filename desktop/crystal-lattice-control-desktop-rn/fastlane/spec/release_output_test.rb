# frozen_string_literal: true

require "minitest/autorun"
require "tmpdir"
require_relative "../release_output"

class MacReleaseOutputTest < Minitest::Test
  def test_first_build_creates_output_without_history
    Dir.mktmpdir do |root|
      output = File.join(root, "macos-release")
      assert_nil CrystalLatticeMacReleaseOutput.prepare(output)
      assert_path_exists output
      refute_path_exists "#{output}-history"
    end
  end

  def test_rebuild_preserves_artifact_and_metadata_across_failed_attempts
    Dir.mktmpdir do |root|
      output = File.join(root, "macos-release")
      Dir.mkdir(output)
      File.binwrite(File.join(output, "candidate.dmg"), "reviewed DMG bytes")
      File.write(File.join(output, "release-metadata.json"), '{"build_number":4}')

      previous = CrystalLatticeMacReleaseOutput.prepare(output)
      retained = File.join(previous, "macos-release")
      assert_equal "reviewed DMG bytes", File.binread(File.join(retained, "candidate.dmg"))
      assert_equal '{"build_number":4}', File.read(File.join(retained, "release-metadata.json"))
      assert_empty Dir.children(output)

      # A failed attempt may leave partial output but must not replace history.
      File.write(File.join(output, "partial-archive"), "incomplete")
      failed = CrystalLatticeMacReleaseOutput.prepare(output)
      refute_equal previous, failed
      assert_equal "incomplete", File.read(File.join(failed, "macos-release", "partial-archive"))
      assert_equal "reviewed DMG bytes", File.binread(File.join(retained, "candidate.dmg"))
      assert_empty Dir.children(output)
    end
  end
end