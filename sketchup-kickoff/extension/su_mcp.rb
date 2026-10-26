require 'sketchup.rb'
require 'extensions.rb'
require 'json'
require 'socket'

module SU_MCP
  unless file_loaded?(__FILE__)
    ex = SketchupExtension.new('Sketchup MCP', 'su_mcp/main')
    ex.description = 'MCP server for Sketchup that allows AI agents to control and manipulate scenes'
    ex.version     = '0.1.0'
    ex.copyright   = '2024'
    Sketchup.register_extension(ex, true)
    file_loaded(__FILE__)

    # [PATCH 2026-10-26] Auto-start MCP Server (skip manual Plugins > MCP Server > Start Server)
    UI.start_timer(3.0, false) {
      begin
        srv = (defined?(SU_MCP) ? SU_MCP.instance_variable_get(:@server) : nil)
        srv.start if srv && !srv.instance_variable_get(:@running)
      rescue => e
        begin
          File.open(File.join(File.dirname(__FILE__), 'su_mcp', 'autostart.log'), 'a') { |f| f.puts("[#{Time.now.strftime('%H:%M:%S')}] failed: #{e.message}") }
        rescue
        end
      end
    }
  end
end 