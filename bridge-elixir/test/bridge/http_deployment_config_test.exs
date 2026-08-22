defmodule Bridge.HttpDeploymentConfigTest do
  use ExUnit.Case, async: true

  test "secure CloudFront edges enable compression and HTTP/2" do
    for path <- [
          "deploy/aws-fargate/secure-edge.yaml",
          "deploy/aws-ec2/secure-edge.yaml"
        ] do
      config = File.read!(path)
      assert config =~ "Compress: true"
      assert config =~ "HttpVersion: http2"
    end
  end

  test "EC2 CloudFront forwards the frontend pairing token header" do
    config = File.read!("deploy/aws-ec2/secure-edge.yaml")
    assert config =~ "X-Crystal-Bridge-Token"
    assert config =~ "X-Crystal-Bridge-Body-Present"
  end

  test "TLS HAProxy advertises HTTP/2 with HTTP/1.1 fallback" do
    config = File.read!("haproxy-ssl.cfg")
    assert config =~ "alpn h2,http/1.1"
  end
end
