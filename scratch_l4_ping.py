from layer4_execution.L4_executor_stub import execute_action

if __name__ == "__main__":
    ok = execute_action("PING", {"example": "payload"})
    print("execute_action('PING') returned:", ok)
