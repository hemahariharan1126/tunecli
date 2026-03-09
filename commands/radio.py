"""Radio command — toggles infinite playback mode."""
from player.playback_controller import get_controller
from rich.console import Console

console = Console()

def radio(args):
    """M!radio [on/off] — toggles endless radio mode."""
    controller = get_controller()
    
    if not args:
        # Toggle current state if no args
        new_state = not controller.radio_mode
    else:
        val = args[0].lower()
        if val in ['on', 'enable', 'true', '1']:
            new_state = True
        elif val in ['off', 'disable', 'false', '0']:
            new_state = False
        else:
            console.print("[yellow]Usage: M!radio [on/off][/yellow]")
            return

    controller.radio_mode = new_state
    
    status = "[bold green]ENABLED[/bold green]" if new_state else "[bold red]DISABLED[/bold red]"
    console.print(f"\n[bold reverse magenta] RADIO.MODE [/bold reverse magenta] {status}")
    
    if new_state:
        console.print("[dim]  TuneCLI will now automatically refill the queue with similar tracks.[/dim]")
        # Trigger initial refill if queue is low
        if len(controller.get_queue()) < 3:
            import threading
            threading.Thread(target=controller._refill_radio, daemon=True).start()
