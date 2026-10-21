# frozen_string_literal: true

require "fileutils"
require "tmpdir"

module CrystalLatticeMacReleaseOutput
  module_function

  # Retain the entire preceding build, including its verification metadata,
  # even if the next archive or notarization fails.
  def prepare(path)
    previous = nil
    if File.exist?(path)
      history = "#{path}-history"
      FileUtils.mkdir_p(history)
      previous = Dir.mktmpdir("#{Time.now.utc.strftime('%Y%m%dT%H%M%SZ')}-", history)
      File.rename(path, File.join(previous, File.basename(path)))
    end
    FileUtils.mkdir_p(path)
    previous
  end
end