game:GetService("CoreGui"):WaitForChild("RobloxPromptGui", math.huge):Destroy()
game.Lighting.ChildAdded:Connect(function(child)
    if child:IsA("BlurEffect") then
        child:Destroy()
        game:GetService("GuiService"):ClearError()
    end
end)
